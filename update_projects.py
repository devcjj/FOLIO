import os
import re
import json
import subprocess
import requests

# Curated featured/static projects that are not fetched directly from GitHub source repos
# (or need custom details like the Figma embed for Orangee)
FEATURED_PROJECTS = [
    {
        "name": "Orangee",
        "category": "design",
        "tag": "UI / UX Design",
        "description": "A complete task-management app design built in Figma; a token-based design system, seven screens, and a clickable prototype.",
        "chips": ["Figma", "Design System"],
        "link": "https://www.figma.com/design/I1WTBcyktZVdtdxtyELhZk/Untitled?node-id=0-1&p=f&t=AexnbBCi64m1Wz5f-0",
        "figma_embed": "https://embed.figma.com/proto/I1WTBcyktZVdtdxtyELhZk/Untitled?node-id=5-559&p=f&scaling=min-zoom&content-scaling=fixed&page-id=4%3A513&starting-point-node-id=5%3A559&embed-host=share"
    },
    {
        "name": "Folio",
        "category": "web",
        "tag": "Front-End Development",
        "description": "A responsive personal portfolio website built using semantic HTML, modern CSS, and JavaScript.",
        "chips": ["HTML", "CSS", "JavaScript"],
        "link": "https://github.com/devcjj/FOLIO"
    },
    {
        "name": "Pulse",
        "category": "code",
        "tag": "Python Automation",
        "description": "A productivity tool that automates weather alerts and morning news digests, runs workflows, and saves time.",
        "chips": ["Python", "Automation"],
        "link": "https://github.com/devcjj/FOLIO"
    }
]

def get_github_username():
    """Tries to extract the GitHub username from the repository's git config."""
    try:
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        # Extract username from 'https://github.com/username/repo' or 'git@github.com:username/repo'
        match = re.search(r"github\.com[:/]([^/]+)/", url)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"Could not retrieve git username from remote config: {e}")
    return "devcjj"  # Fallback username

def format_project_name(name):
    """Formats raw repository names like 'IMPOSTER-WORD' into 'Imposter Word'."""
    # Split by hyphens or underscores
    words = name.replace("-", " ").replace("_", " ").split()
    # Capitalize each word
    return " ".join(w.capitalize() for w in words)

def map_repo_to_project(repo):
    """Maps GitHub API repo object fields to our project structure."""
    name = repo.get("name", "")
    formatted_name = format_project_name(name)
    description = repo.get("description") or "A public GitHub repository."
    lang = repo.get("language")
    link = repo.get("html_url", "#")
    topics = repo.get("topics", [])
    
    # Map primary language to category and tag
    lang_lower = lang.lower() if lang else ""
    if lang_lower in ["html", "css", "javascript", "typescript", "vue", "react"]:
        category = "web"
        tag = "Web Development"
    elif lang_lower in ["python"]:
        category = "code"
        tag = "Python Development"
    elif lang_lower in ["c++", "c", "java", "go", "rust", "c#"]:
        category = "code"
        tag = f"{lang} Development"
    else:
        category = "code"
        tag = "Software Project"

    # Assemble tech chips (limit to 3)
    chips = []
    if lang:
        chips.append(lang)
    for t in topics:
        topic_display = t.replace("-", " ").title()
        if topic_display not in chips:
            chips.append(topic_display)
    if not chips:
        chips = ["GitHub"]
    chips = chips[:3]
    
    return {
        "name": formatted_name,
        "category": category,
        "tag": tag,
        "description": description,
        "chips": chips,
        "link": link
    }

def fetch_github_repos(username):
    """Fetches public repositories from the GitHub API."""
    url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=pushed"
    headers = {"User-Agent": "Portfolio-Updater"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
        
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Failed to fetch repositories from GitHub API: {e}")
        return []

def generate_card_html(project):
    """Generates the HTML markup for a single project card."""
    category = project["category"]
    tag = project["tag"]
    name = project["name"]
    description = project["description"]
    chips = project["chips"]
    link = project["link"]
    figma_embed = project.get("figma_embed")

    chips_html = "".join(f'\n                            <span class="chip">{c}</span>' for c in chips)

    figma_button_html = ""
    figma_drawer_html = ""
    if figma_embed:
        figma_button_html = f"""
                            <button class="btn-preview-toggle" aria-expanded="false"
                                aria-label="Toggle Figma live preview">
                                Live Preview <span class="preview-icon">▼</span>
                            </button>"""
        figma_drawer_html = f"""

                        <!-- Live Preview Drawer -->
                        <div class="preview-drawer">
                            <div class="preview-iframe-wrapper">
                                <iframe class="figma-embed" src=""
                                    data-src="{figma_embed}"
                                    allowfullscreen>
                                </iframe>
                            </div>
                        </div>"""

    card_html = f"""
                    <!-- Project Card: {name} -->
                    <article class="card reveal" data-category="{category}">

                        <span class="card-tag">
                            {tag}
                        </span>

                        <h3 class="card-title">
                            {name}
                        </h3>

                        <p class="card-desc">
                            {description}
                        </p>

                        <div class="card-meta">{chips_html}
                        </div>

                        <div class="card-actions">
                            <a href="{link}" target="_blank" rel="noopener" class="card-link">
                                View Project <span class="arrow">→</span>
                            </a>{figma_button_html}
                        </div>{figma_drawer_html}

                    </article>"""
    return card_html

def update_index_html(project_list):
    """Injects the generated HTML card markup into index.html between the markers."""
    html_filename = "index.html"
    if not os.path.exists(html_filename):
        print(f"Error: {html_filename} not found.")
        return False
        
    with open(html_filename, "r", encoding="utf-8") as f:
        content = f.read()

    start_marker = "<!-- PROJECTS_START -->"
    end_marker = "<!-- PROJECTS_END -->"

    if start_marker not in content or end_marker not in content:
        print(f"Error: Markers '{start_marker}' or '{end_marker}' not found in {html_filename}.")
        return False

    # Build the HTML block for all projects
    cards_html = "\n".join(generate_card_html(p) for p in project_list)
    
    # Locate indices and slice the string to replace content in between markers
    start_idx = content.find(start_marker) + len(start_marker)
    end_idx = content.find(end_marker)
    
    updated_content = content[:start_idx] + "\n" + cards_html + "\n                    " + content[end_idx:]
    
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(updated_content)
        
    print(f"Successfully updated project cards in {html_filename}.")
    return True

def run():
    username = get_github_username()
    print(f"Updating projects list for GitHub user: {username}")
    
    # Fetch public repositories
    repos = fetch_github_repos(username)
    
    # Map repositories to our project layout, filtering out:
    # 1. Forked repositories (to keep it focused on original work)
    # 2. FOLIO repository itself (already manually added to the featured projects)
    dyn_projects = []
    for r in repos:
        if r.get("fork"):
            continue
        name = r.get("name", "")
        if name.lower() == "folio":
            continue
        dyn_projects.append(map_repo_to_project(r))
        
    print(f"Fetched {len(dyn_projects)} repositories from GitHub API.")

    # Combine static/featured projects with dynamic repositories
    all_projects = FEATURED_PROJECTS + dyn_projects

    # Save to projects.json
    json_filename = "projects.json"
    try:
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(all_projects, f, indent=4)
        print(f"Successfully generated {json_filename}.")
    except Exception as e:
        print(f"Error generating {json_filename}: {e}")

    # Inject project HTML cards into index.html
    update_index_html(all_projects)

if __name__ == "__main__":
    run()
