(function() {
    const featureNames = [
        "txCount","inTxCount","outTxCount","totalInAmount","totalOutAmount",
        "uniqueCounterparties","velocity","avgTxAmount","amountStdDev",
        "rapidHoldingRatio","inOutRatio","behavioralShift","networkDegree",
        "inboundDegree","outboundDegree","isFanIn","isFanOut","sharedSuspiciousConnection",
        "totalDegree","fanIn","fanOut","networkConcentration","cycleParticipation",
        "multiHopConnectivity","temporalProximity","activityPattern"
    ];

    // Human-readable labels for the 26 ML features
    const FEATURE_LABELS = {
        txCount:                    "Transaction Count",
        inTxCount:                  "Inbound Tx Count",
        outTxCount:                 "Outbound Tx Count",
        totalInAmount:              "Total Inbound (\u20b9)",
        totalOutAmount:             "Total Outbound (\u20b9)",
        uniqueCounterparties:       "Unique Counterparties",
        velocity:                   "Transaction Velocity",
        avgTxAmount:                "Avg Tx Amount (\u20b9)",
        amountStdDev:               "Amount Std Deviation",
        rapidHoldingRatio:          "Short Holding Ratio (%)",
        inOutRatio:                 "Inbound/Outbound Ratio",
        behavioralShift:            "Behavioural Shift",
        networkDegree:              "Network Degree",
        inboundDegree:              "Inbound Degree",
        outboundDegree:             "Outbound Degree",
        isFanIn:                    "Fan-In Pattern",
        isFanOut:                   "Fan-Out Pattern",
        sharedSuspiciousConnection: "Shared Suspicious Connection",
        totalDegree:                "Total Degree",
        fanIn:                      "Fan-In Counterparties",
        fanOut:                     "Fan-Out Counterparties",
        networkConcentration:       "Network Concentration (HHI)",
        cycleParticipation:         "Cycle Participation",
        multiHopConnectivity:       "Multi-Hop Connectivity",
        temporalProximity:          "Temporal Proximity (min)",
        activityPattern:            "Recent Activity Pattern"
    };

    function sigmoid(x) {
        return 1.0 / (1.0 + Math.exp(-x));
    }

    function predictRisk(featuresObj, model) {
        if (!model || !model.learner || !model.learner.gradient_booster || !model.learner.gradient_booster.model) {
            console.error("XGBoost Model is not loaded or invalid.");
            return null;
        }

        // Get base score from model parameters
        let baseScore = 0.5;
        if (model.learner.learner_model_param && model.learner.learner_model_param.base_score) {
            const rawBase = model.learner.learner_model_param.base_score;
            // Parse "[3.0927834E-1]" or float representation
            const parsedBase = parseFloat(rawBase.replace('[', '').replace(']', ''));
            if (!isNaN(parsedBase)) {
                baseScore = parsedBase;
            }
        }
        
        // Convert base score probability to log-odds
        let rawScore = Math.log(baseScore / (1.0 - baseScore));

        const trees = model.learner.gradient_booster.model.trees;
        if (!trees) {
            console.error("No trees found in XGBoost model.");
            return null;
        }

        // Traverse each tree in the ensemble
        for (let i = 0; i < trees.length; i++) {
            const tree = trees[i];
            let nodeId = 0; // Start at root node of the tree
            
            // Loop until we hit a leaf node (leaf nodes have left_children[nodeId] === -1)
            while (true) {
                const leftChild = tree.left_children[nodeId];
                const rightChild = tree.right_children[nodeId];
                
                if (leftChild === -1 || rightChild === -1) {
                    // Leaf node reached: retrieve weight from base_weights
                    const leafWeight = tree.base_weights[nodeId];
                    rawScore += leafWeight;
                    break;
                }

                // Split node: retrieve split feature index and threshold condition
                const splitIndex = tree.split_indices[nodeId];
                const splitCondition = tree.split_conditions[nodeId];
                
                // Get feature name and value from featuresObj
                const fName = featureNames[splitIndex];
                let fVal = featuresObj[fName];
                
                // Handle missing values (XGBoost uses default_left to route missing values)
                if (fVal === undefined || fVal === null || isNaN(fVal)) {
                    const isDefaultLeft = tree.default_left[nodeId] === 1;
                    nodeId = isDefaultLeft ? leftChild : rightChild;
                } else {
                    // Evaluate binary split condition: x < threshold
                    if (fVal < splitCondition) {
                        nodeId = leftChild;
                    } else {
                        nodeId = rightChild;
                    }
                }
            }
        }

        // Return sigmoidal probability
        return sigmoid(rawScore);
    }

    // ── predictRiskWithFeatures ──────────────────────────────────────────────
    // Parallel explainability function. Runs the same tree traversal as
    // predictRisk() but additionally counts split-node visits per feature.
    // Returns { probability, topFeatures[] } where topFeatures are the 5
    // features most frequently visited across all tree split nodes.
    // The existing predictRisk() function is NOT called or modified.
    function predictRiskWithFeatures(featuresObj, model) {
        if (!model || !model.learner || !model.learner.gradient_booster || !model.learner.gradient_booster.model) {
            return null;
        }

        // Base score (same as predictRisk)
        let baseScore = 0.5;
        if (model.learner.learner_model_param && model.learner.learner_model_param.base_score) {
            const parsedBase = parseFloat(
                model.learner.learner_model_param.base_score.replace('[', '').replace(']', '')
            );
            if (!isNaN(parsedBase)) baseScore = parsedBase;
        }
        let rawScore = Math.log(baseScore / (1.0 - baseScore));

        const trees = model.learner.gradient_booster.model.trees;
        if (!trees) return null;

        // Feature visit counter (by index)
        const visitCount = new Array(featureNames.length).fill(0);

        for (let i = 0; i < trees.length; i++) {
            const tree = trees[i];
            let nodeId = 0;

            while (true) {
                const leftChild  = tree.left_children[nodeId];
                const rightChild = tree.right_children[nodeId];

                if (leftChild === -1 || rightChild === -1) {
                    rawScore += tree.base_weights[nodeId];
                    break;
                }

                const splitIndex     = tree.split_indices[nodeId];
                const splitCondition = tree.split_conditions[nodeId];

                // Count this feature visit
                if (splitIndex >= 0 && splitIndex < featureNames.length) {
                    visitCount[splitIndex]++;
                }

                const fName = featureNames[splitIndex];
                let fVal = featuresObj[fName];

                if (fVal === undefined || fVal === null || isNaN(fVal)) {
                    const isDefaultLeft = tree.default_left[nodeId] === 1;
                    nodeId = isDefaultLeft ? leftChild : rightChild;
                } else {
                    nodeId = fVal < splitCondition ? leftChild : rightChild;
                }
            }
        }

        const probability = sigmoid(rawScore);

        // Build top-5 features sorted by visit count descending
        const indexed = visitCount.map((cnt, idx) => ({ idx, cnt }));
        indexed.sort((a, b) => b.cnt - a.cnt);
        const topFeatures = indexed.slice(0, 5).map(item => {
            const name  = featureNames[item.idx];
            const label = FEATURE_LABELS[name] || name;
            const value = featuresObj[name];
            return { name, label, value: (value !== undefined && value !== null) ? value : 0 };
        });

        return { probability, topFeatures };
    }

    // Export to window object
    if (typeof window !== 'undefined') {
        window.MuleGuardXGBoost = {
            predictRisk:             predictRisk,
            predictRiskWithFeatures: predictRiskWithFeatures,
            featureNames:            featureNames,
            featureLabels:           FEATURE_LABELS
        };
    }
    
    // Node.js support for validation scripts
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            predictRisk:             predictRisk,
            predictRiskWithFeatures: predictRiskWithFeatures,
            featureNames:            featureNames,
            featureLabels:           FEATURE_LABELS
        };
    }
})();
