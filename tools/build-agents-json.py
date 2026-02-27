#!/usr/bin/env python3
"""Parse agent markdown files and generate agents.json for the web UI."""

import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DIVISIONS = {
    "engineering": {"label": "Engineering", "emoji": "💻", "order": 0},
    "design": {"label": "Design", "emoji": "🎨", "order": 1},
    "marketing": {"label": "Marketing", "emoji": "📢", "order": 2},
    "product": {"label": "Product", "emoji": "📦", "order": 3},
    "project-management": {"label": "Project Management", "emoji": "📋", "order": 4},
    "testing": {"label": "Testing", "emoji": "🧪", "order": 5},
    "support": {"label": "Support", "emoji": "🛟", "order": 6},
    "spatial-computing": {"label": "Spatial Computing", "emoji": "🥽", "order": 7},
    "specialized": {"label": "Specialized", "emoji": "🎯", "order": 8},
}

# Map agent filenames to the emoji used in README roster table
AGENT_EMOJIS = {
    "engineering-frontend-developer": "🎨",
    "engineering-backend-architect": "🏗️",
    "engineering-mobile-app-builder": "📱",
    "engineering-ai-engineer": "🤖",
    "engineering-devops-automator": "🚀",
    "engineering-rapid-prototyper": "⚡",
    "engineering-senior-developer": "💎",
    "design-ui-designer": "🎯",
    "design-ux-researcher": "🔍",
    "design-ux-architect": "🏛️",
    "design-brand-guardian": "🎭",
    "design-visual-storyteller": "📖",
    "design-whimsy-injector": "✨",
    "marketing-growth-hacker": "🚀",
    "marketing-content-creator": "📝",
    "marketing-twitter-engager": "🐦",
    "marketing-tiktok-strategist": "🎵",
    "marketing-instagram-curator": "📸",
    "marketing-reddit-community-builder": "🤝",
    "marketing-app-store-optimizer": "📲",
    "marketing-social-media-strategist": "📣",
    "product-sprint-prioritizer": "🏃",
    "product-trend-researcher": "🔮",
    "product-feedback-synthesizer": "🧲",
    "project-management-studio-producer": "🎬",
    "project-management-project-shepherd": "🐑",
    "project-management-studio-operations": "⚙️",
    "project-management-experiment-tracker": "🧪",
    "project-manager-senior": "👔",
    "testing-evidence-collector": "📸",
    "testing-reality-checker": "🔍",
    "testing-test-results-analyzer": "📊",
    "testing-performance-benchmarker": "⏱️",
    "testing-api-tester": "🔌",
    "testing-tool-evaluator": "🛠️",
    "testing-workflow-optimizer": "🔄",
    "support-support-responder": "💬",
    "support-analytics-reporter": "📊",
    "support-finance-tracker": "💰",
    "support-infrastructure-maintainer": "🖥️",
    "support-legal-compliance-checker": "⚖️",
    "support-executive-summary-generator": "📄",
    "xr-interface-architect": "🥽",
    "macos-spatial-metal-engineer": "🍎",
    "xr-immersive-developer": "🌐",
    "xr-cockpit-interaction-specialist": "🎮",
    "visionos-spatial-engineer": "🍎",
    "terminal-integration-specialist": "🔌",
    "agents-orchestrator": "🎭",
    "data-analytics-reporter": "📊",
    "lsp-index-engineer": "🔍",
}

COLOR_MAP = {
    "cyan": "#06b6d4",
    "pink": "#ec4899",
    "red": "#ef4444",
    "green": "#22c55e",
    "blue": "#3b82f6",
    "teal": "#14b8a6",
    "purple": "#a855f7",
    "orange": "#f97316",
    "yellow": "#eab308",
    "indigo": "#6366f1",
}


def parse_frontmatter(content):
    """Extract YAML frontmatter from markdown content."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return {}, content
    fm_text = match.group(1)
    body = content[match.end():]
    fm = {}
    for line in fm_text.strip().split("\n"):
        if ":" in line:
            key, val = line.split(":", 1)
            fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm, body


def extract_heading(body):
    """Extract the first markdown heading."""
    match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    return match.group(1).strip() if match else None


def extract_section(body, emoji_or_heading):
    """Extract a section by its emoji or heading pattern."""
    pattern = rf"^##\s+.*{re.escape(emoji_or_heading)}.*$"
    match = re.search(pattern, body, re.MULTILINE)
    if not match:
        return None
    start = match.end()
    next_heading = re.search(r"^##\s+", body[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(body)
    return body[start:end].strip()


def extract_identity(body):
    """Extract role and personality from identity section."""
    # Try emoji-based Identity section first
    section = extract_section(body, "Identity")
    if not section:
        match = re.search(r"^##.*Identity.*$", body, re.MULTILINE | re.IGNORECASE)
        if match:
            start = match.end()
            next_h = re.search(r"^##\s+", body[start:], re.MULTILINE)
            end = start + next_h.start() if next_h else len(body)
            section = body[start:end].strip()

    role = None
    personality = None

    if section:
        for line in section.split("\n"):
            if "**Role**" in line or "**role**" in line:
                role = re.sub(r".*\*\*[Rr]ole\*\*:?\s*", "", line).strip()
            if "**Personality**" in line or "**personality**" in line:
                personality = re.sub(r".*\*\*[Pp]ersonality\*\*:?\s*", "", line).strip()

    # Fallback: try "## Role Definition" section (used by marketing, product, specialized agents)
    if not role:
        role_section = extract_section(body, "Role Definition")
        if not role_section:
            match = re.search(r"^##\s+Role Definition.*$", body, re.MULTILINE | re.IGNORECASE)
            if match:
                start = match.end()
                next_h = re.search(r"^##\s+", body[start:], re.MULTILINE)
                end = start + next_h.start() if next_h else len(body)
                role_section = body[start:end].strip()
        if role_section:
            # The role definition is typically the first paragraph
            first_line = role_section.split("\n")[0].strip()
            if first_line and not first_line.startswith("-") and not first_line.startswith("#"):
                role = first_line

    # Fallback: try **Specialization** (spatial-computing style)
    if not role:
        match = re.search(r"\*\*Specialization\*\*:?\s*(.+)", body)
        if match:
            role = match.group(1).strip()

    # Fallback: try **Core Identity**: line (instagram-curator style)
    if not role:
        match = re.search(r"\*\*Core Identity\*\*:?\s*(.+)", body)
        if match:
            role = match.group(1).strip()

    # Fallback: try Identity & Memory section as paragraph (non-emoji style)
    if not role:
        id_section = extract_section(body, "Identity")
        if id_section:
            for line in id_section.split("\n"):
                line = line.strip()
                if line and not line.startswith("-") and not line.startswith("#") and not line.startswith("*"):
                    if len(line) > 30:
                        role = line[:150]
                        break

    # Extract personality from "## Specialized Skills" as fallback (first 3 items)
    if not personality:
        skills_section = extract_section(body, "Specialized Skills")
        if not skills_section:
            match = re.search(r"^##\s+Specialized Skills.*$", body, re.MULTILINE | re.IGNORECASE)
            if match:
                start = match.end()
                next_h = re.search(r"^##\s+", body[start:], re.MULTILINE)
                end = start + next_h.start() if next_h else len(body)
                skills_section = body[start:end].strip()
        if skills_section:
            skills = []
            for line in skills_section.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    skill = line[2:].strip()
                    # Shorten long skill descriptions
                    if len(skill) > 60:
                        skill = skill[:57] + "..."
                    skills.append(skill)
                    if len(skills) >= 3:
                        break
            if skills:
                personality = "; ".join(skills)

    return role, personality


def extract_mission_bullets(body):
    """Extract core mission section as a list of key responsibilities."""
    # Try multiple heading patterns
    section = None
    for heading_kw in ["Core Mission", "Core Capabilities", "Core Responsibilities", "Core Expertise"]:
        section = extract_section(body, heading_kw)
        if section:
            break
    if not section:
        for pattern in [r"Core Mission", r"Core Capabilities", r"Core Responsibilities", r"Core Expertise"]:
            match = re.search(rf"^##\s+.*{pattern}.*$", body, re.MULTILINE | re.IGNORECASE)
            if match:
                start = match.end()
                next_h = re.search(r"^##\s+", body[start:], re.MULTILINE)
                end = start + next_h.start() if next_h else len(body)
                section = body[start:end].strip()
                break
    if not section:
        return []

    bullets = []

    # Pattern 1: ### Emoji Title (used by engineering/design/support agents)
    for line in section.split("\n"):
        line = line.strip()
        if line.startswith("### "):
            title = re.sub(r"^###\s+\S+\s*", "", line).strip()
            if title:
                bullets.append(title)

    # Pattern 2: numbered list items
    if not bullets:
        for line in section.split("\n"):
            line = line.strip()
            if re.match(r"^\d+\.", line):
                text = re.sub(r"^\d+\.\s*", "", line).strip()
                text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
                if text:
                    bullets.append(text)

    # Pattern 3: - **Bold Key**: description (used by marketing/product/specialized)
    if not bullets:
        for line in section.split("\n"):
            line = line.strip()
            match = re.match(r"^-\s+\*\*(.+?)\*\*", line)
            if match:
                bullets.append(match.group(1))

    # Pattern 4: ### Sub-headings without emoji prefix
    if not bullets:
        for line in section.split("\n"):
            line = line.strip()
            if line.startswith("### "):
                title = re.sub(r"^###\s+", "", line).strip()
                if title:
                    bullets.append(title)

    return bullets[:5]


def extract_mission_bullets_fallback(body):
    """Fallback mission extraction: scan all ## sections for ### sub-headings or bold bullets."""
    bullets = []
    # Scan entire body for ### headings under any ## section
    for match in re.finditer(r"^###\s+(.+)$", body, re.MULTILINE):
        title = match.group(1).strip()
        # Remove leading emoji
        title = re.sub(r"^[\U0001F000-\U0001FFFF\u2600-\u27FF\u2700-\u27BF\uFE00-\uFE0F]\s*", "", title).strip()
        # Remove quotes
        title = title.strip('"').strip("'")
        if title and len(title) > 3 and len(title) < 80:
            bullets.append(title)
        if len(bullets) >= 5:
            break
    return bullets[:5]


def normalize_color(color_str):
    """Convert color names to hex values."""
    if not color_str:
        return "#6366f1"
    color_str = color_str.lower().strip()
    if color_str.startswith("#"):
        return color_str
    return COLOR_MAP.get(color_str, "#6366f1")


# Manual name overrides for agents with tricky frontmatter names
NAME_OVERRIDES = {
    "engineering-ai-engineer": "AI Engineer",
    "design-ux-architect": "UX Architect",
    "project-manager-senior": "Senior Project Manager",
    "testing-evidence-collector": "Evidence Collector",
    "marketing-tiktok-strategist": "TikTok Strategist",
    "macos-spatial-metal-engineer": "macOS Spatial/Metal Engineer",
    "visionos-spatial-engineer": "visionOS Spatial Engineer",
    "lsp-index-engineer": "LSP/Index Engineer",
    "xr-interface-architect": "XR Interface Architect",
    "xr-immersive-developer": "XR Immersive Developer",
    "xr-cockpit-interaction-specialist": "XR Cockpit Interaction Specialist",
}


def prettify_name(filename_stem, fm_name=None):
    """Generate a clean display name from frontmatter or filename."""
    # Check overrides first
    if filename_stem in NAME_OVERRIDES:
        return NAME_OVERRIDES[filename_stem]

    if fm_name:
        # Remove division prefixes from frontmatter name
        for prefix in ["engineering-", "design-", "marketing-", "product-", "testing-",
                        "support-", "project-management-", "project-manager-", "pm-"]:
            if fm_name.lower().startswith(prefix):
                fm_name = fm_name[len(prefix):]
                break
        # If it looks like a slug, titleize it
        if "-" in fm_name and fm_name == fm_name.lower():
            return fm_name.replace("-", " ").title()
        return fm_name
    return filename_stem.replace("-", " ").title()


def parse_agent_file(filepath, division_key):
    """Parse a single agent markdown file into a data dict."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    fm, body = parse_frontmatter(content)
    filename = os.path.basename(filepath)
    stem = os.path.splitext(filename)[0]

    heading = extract_heading(body)
    name = fm.get("name") or heading or stem
    name = prettify_name(stem, name)

    description = fm.get("description", "")
    color = normalize_color(fm.get("color"))
    role, personality = extract_identity(body)
    missions = extract_mission_bullets(body)
    if not missions:
        missions = extract_mission_bullets_fallback(body)
    emoji = AGENT_EMOJIS.get(stem, "🤖")

    # Fallback: use role as description if no frontmatter description
    if not description and role:
        description = role

    # Fallback: derive description from the first non-heading paragraph
    if not description:
        for line in body.split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("-") and not line.startswith("*"):
                description = line
                break

    return {
        "id": stem,
        "name": name,
        "emoji": emoji,
        "description": description,
        "color": color,
        "division": division_key,
        "file": f"{division_key}/{filename}",
        "role": role,
        "personality": personality,
        "missions": missions,
    }


def main():
    agents = []
    for div_key, div_info in sorted(DIVISIONS.items(), key=lambda x: x[1]["order"]):
        div_path = os.path.join(REPO_ROOT, div_key)
        if not os.path.isdir(div_path):
            print(f"Warning: Division directory not found: {div_path}", file=sys.stderr)
            continue
        for filename in sorted(os.listdir(div_path)):
            if not filename.endswith(".md"):
                continue
            filepath = os.path.join(div_path, filename)
            try:
                agent = parse_agent_file(filepath, div_key)
                agents.append(agent)
            except Exception as e:
                print(f"Error parsing {filepath}: {e}", file=sys.stderr)

    divisions = []
    for div_key, div_info in sorted(DIVISIONS.items(), key=lambda x: x[1]["order"]):
        count = sum(1 for a in agents if a["division"] == div_key)
        divisions.append({
            "id": div_key,
            "label": div_info["label"],
            "emoji": div_info["emoji"],
            "count": count,
        })

    output = {
        "divisions": divisions,
        "agents": agents,
    }

    out_path = os.path.join(REPO_ROOT, "docs", "agents.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Generated {out_path} with {len(agents)} agents across {len(divisions)} divisions")


if __name__ == "__main__":
    main()
