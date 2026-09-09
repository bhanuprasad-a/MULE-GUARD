import os
import re

bank_dir = "frontend/bank/investigator"
bank_files = [f for f in os.listdir(bank_dir) if f.endswith(".html")]

def generate_nav_block(active_page):
    def active_classes(is_active):
        if is_active:
            return 'flex items-center gap-3 px-3 py-2.5 rounded-lg text-on-primary font-body-md text-[14px] bg-secondary-container/25 border-l-2 border-secondary-container hover:bg-secondary-container/30 transition-all duration-150'
        else:
            return 'flex items-center gap-3 px-3 py-2.5 rounded-lg text-on-primary-container/70 font-body-md text-[14px] hover:bg-secondary-container/10 hover:text-on-primary border-l-2 border-transparent transition-all duration-150'
    
    def active_icon_classes(is_active):
        if is_active:
            return 'material-symbols-outlined text-[20px] text-secondary-container'
        else:
            return 'material-symbols-outlined text-[20px]'

    nav_html = f'''<nav class="flex-1 px-4 py-6 space-y-7">
                                <!-- Command Center Group -->
                                <div class="space-y-1">
                                        <div class="px-3 mb-2">
                                                <span class="font-mono-technical text-[10px] text-on-primary-container tracking-wider uppercase opacity-55">Command Center</span>
                                        </div>
                                        <!-- Active State Indicators -->
                                        <a href="dashboard.html" class="{active_classes(active_page == 'dashboard')}">
                                                <span class="{active_icon_classes(active_page == 'dashboard')}">dashboard</span>
                                                <span class="{"font-medium" if active_page == 'dashboard' else ''}">Dashboard</span>
                                        </a>
                                        <a href="investigations.html" class="{active_classes(active_page == 'investigations')}">
                                                <span class="{active_icon_classes(active_page == 'investigations')}">search_insights</span>
                                                <span class="{"font-medium" if active_page == 'investigations' else ''}">Investigations</span>
                                        </a>
                                        <a href="alerts.html" class="{active_classes(active_page == 'alerts')}">
                                                <span class="{active_icon_classes(active_page == 'alerts')}">notifications_active</span>
                                                <span class="{"font-medium" if active_page == 'alerts' else ''}">Alerts</span>
                                        </a>
                                        <a href="cases.html" class="{active_classes(active_page == 'cases')}">
                                                <span class="{active_icon_classes(active_page == 'cases')}">work</span>
                                                <span class="{"font-medium" if active_page == 'cases' else ''}">Cases</span>
                                        </a>
                                </div>
                        </nav>'''
    return nav_html

for filename in bank_files:
    filepath = os.path.join(bank_dir, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Clear old guard if any, insert updated depth guard
    content = re.sub(r'<!-- Authentication Guard -->\s*<script src=".*?auth-guard.js"></script>', '', content)
    if 'scripts/auth-guard.js' not in content:
        content = content.replace("<head>", '<head>\n        <!-- Authentication Guard -->\n        <script src="../../scripts/auth-guard.js"></script>')

    # Update stylesheet path
    content = content.replace('href="style.css"', 'href="../../style.css"')
    content = content.replace('href="../style.css"', 'href="../../style.css"')

    # Update logo and asset paths
    content = content.replace('src="../assets/', 'src="../../../assets/')
    content = content.replace('src="../../assets/', 'src="../../../assets/')

    # Update Sign Out link to window.logoutUser()
    content = content.replace('href="login.html"', 'href="#" onclick="logoutUser()"')
    content = content.replace('href="../login.html"', 'href="#" onclick="logoutUser()"')

    # Update sidebar navigation
    active_page_name = filename.replace(".html", "")
    nav_pattern = re.compile(r'<nav class="flex-1 px-4 py-6 space-y-7">.*?</nav>', re.DOTALL)
    new_nav = generate_nav_block(active_page_name)
    content = nav_pattern.sub(new_nav, content)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Migrated investigator page: {filename}")

print("Migration completed successfully.")
