module.exports = {
  content: ["./frontend/**/*.html", "./frontend/**/*.js"],
  theme: {
    extend: {
      colors: {
        "primary-fixed": "#d6e3ff",
        "secondary-fixed-dim": "#b4c5ff",
        "error-container": "#ffdad6",
        "surface-container-highest": "#e0e3e6",
        "primary-container": "#0b1f3a",
        "on-surface-variant": "#44474d",
        "tertiary": "#00070e",
        "on-secondary-container": "#fefcff",
        "surface-container-high": "#e6e8eb",
        "on-surface": "#191c1e",
        "on-primary-fixed": "#071c36",
        "surface-container-lowest": "#ffffff",
        "inverse-on-surface": "#eff1f4",
        "surface-variant": "#e0e3e6",
        "surface-container": "#eceef1",
        "on-primary-container": "#7587a7",
        "surface": "#f7f9fc",
        "on-tertiary-fixed": "#001e2c",
        "on-secondary-fixed-variant": "#003ea8",
        "risk-high": "#EF4444",
        "surface-container-low": "#f2f4f7",
        "outline-variant": "#c4c6ce",
        "background": "#f7f9fc",
        "surface-bright": "#f7f9fc",
        "secondary-container": "#316bf3",
        "outline": "#75777e",
        "tertiary-container": "#002231",
        "inverse-surface": "#2d3133",
        "error": "#ba1a1a",
        "secondary": "#0051d5",
        "on-tertiary": "#ffffff",
        "interface-base": "#FFFFFF",
        "inverse-primary": "#b5c7ea",
        "on-tertiary-fixed-variant": "#004c69",
        "on-error-container": "#93000a",
        "risk-low": "#10B981",
        "on-background": "#191c1e",
        "tertiary-fixed-dim": "#7bd0ff",
        "on-primary-fixed-variant": "#364764",
        "tertiary-fixed": "#c4e7ff",
        "surface-tint": "#4d5f7d",
        "primary-fixed-dim": "#b5c7ea",
        "on-secondary-fixed": "#00174b",
        "on-error": "#ffffff",
        "on-primary": "#ffffff",
        "on-tertiary-container": "#0091c3",
        "secondary-fixed": "#dbe1ff",
        "surface-dim": "#d8dadd",
        "primary": "#000615",
        "on-secondary": "#ffffff"
      },
      borderRadius: {
        DEFAULT: "0.25rem",
        lg: "0.5rem",
        xl: "0.75rem",
        full: "9999px"
      },
      spacing: {
        gutter: "32px",
        "container-padding-mobile": "24px",
        "stack-gap": "24px",
        "container-padding-desktop": "64px",
        unit: "4px"
      },
      fontFamily: {
        "headline-lg": ["Inter"],
        "body-lg": ["Inter"],
        "label-sm": ["Inter"],
        "label-md": ["Inter"],
        "body-md": ["Inter"],
        "mono-technical": ["Inter"],
        "headline-md": ["Inter"],
        "display-lg": ["Inter"]
      },
      fontSize: {
        "headline-lg": [
          "32px",
          {
            lineHeight: "40px",
            letterSpacing: "-0.01em",
            fontWeight: "700"
          }
        ],
        "body-lg": [
          "18px",
          {
            lineHeight: "28px",
            fontWeight: "400"
          }
        ],
        "label-sm": [
          "12px",
          {
            lineHeight: "16px",
            letterSpacing: "0.05em",
            fontWeight: "500"
          }
        ],
        "label-md": [
          "14px",
          {
            lineHeight: "20px",
            fontWeight: "600"
          }
        ],
        "body-md": [
          "16px",
          {
            lineHeight: "24px",
            fontWeight: "400"
          }
        ],
        "mono-technical": [
          "11px",
          {
            lineHeight: "16px",
            letterSpacing: "0.1em",
            fontWeight: "500"
          }
        ],
        "headline-md": [
          "24px",
          {
            lineHeight: "32px",
            fontWeight: "700"
          }
        ],
        "display-lg": [
          "48px",
          {
            lineHeight: "56px",
            letterSpacing: "-0.02em",
            fontWeight: "800"
          }
        ]
      }
    }
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/container-queries")
  ]
};
