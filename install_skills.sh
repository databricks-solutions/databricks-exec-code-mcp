#!/bin/bash
#
# Databricks MCP Skills Installer
#
# Installs skills to Claude Code (.claude/skills/) and/or Cursor (.cursor/rules/).
# Skills are auto-discovered from the skills/ directory.
#
# Usage:
#   ./install_skills.sh --claude              # Install to .claude/skills/
#   ./install_skills.sh --cursor              # Install to .cursor/rules/
#   ./install_skills.sh --all                 # Install to both
#   ./install_skills.sh --all --local         # Install from local skills/ directory
#   ./install_skills.sh --list                # List available skills
#   ./install_skills.sh --help                # Show help
#
# Remote install (one-liner):
#   curl -sSL https://raw.githubusercontent.com/databricks-solutions/databricks-exec-code-mcp/main/install_skills.sh | bash -s -- --all
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_RAW_URL="https://raw.githubusercontent.com/databricks-solutions/databricks-exec-code-mcp/main"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SOURCE_DIR="skills"

# Output directories
CLAUDE_SKILLS_DIR=".claude/skills"
CURSOR_RULES_DIR=".cursor/rules"

# Flags
INSTALL_CLAUDE=false
INSTALL_CURSOR=false
INSTALL_FROM_LOCAL=false
LIST_ONLY=false

# ============================================================
# Helper Functions
# ============================================================

show_help() {
    echo -e "${BLUE}Databricks MCP Skills Installer${NC}"
    echo ""
    echo "Installs Databricks skills for Claude Code and/or Cursor."
    echo "Run this in your project directory."
    echo ""
    echo -e "${YELLOW}Usage:${NC}"
    echo "  ./install_skills.sh --claude              # Install to .claude/skills/"
    echo "  ./install_skills.sh --cursor              # Install to .cursor/rules/"
    echo "  ./install_skills.sh --all                 # Install to both"
    echo "  ./install_skills.sh --all --local         # Install from local skills/ directory"
    echo "  ./install_skills.sh --list                # List available skills"
    echo "  ./install_skills.sh --help                # Show this help"
    echo ""
    echo -e "${YELLOW}Remote install (one-liner):${NC}"
    echo "  curl -sSL ${REPO_RAW_URL}/install_skills.sh | bash -s -- --all"
    echo ""
    echo -e "${YELLOW}Options:${NC}"
    echo "  --claude       Install skills to .claude/skills/ (for Claude Code)"
    echo "  --cursor       Install skills to .cursor/rules/ (for Cursor)"
    echo "  --all          Install to both Claude and Cursor"
    echo "  --local        Use local skills/ directory instead of downloading"
    echo "  --list, -l     List available skills"
    echo "  --help, -h     Show this help message"
    echo ""
}

# Extract value from YAML frontmatter
# Usage: extract_frontmatter "field_name" "file_path"
extract_frontmatter() {
    local field="$1"
    local file="$2"
    
    # Extract content between --- markers, then get the field value
    awk -v field="$field" '
        BEGIN { in_frontmatter=0; found=0 }
        /^---$/ { 
            if (!found) in_frontmatter = !in_frontmatter
            next
        }
        in_frontmatter {
            # Match field: value (handles quoted and unquoted values)
            if ($0 ~ "^" field ":") {
                sub("^" field ":[[:space:]]*", "")
                gsub(/^["'\'']|["'\'']$/, "")  # Remove quotes
                print
                found=1
                exit
            }
        }
    ' "$file"
}

# Get list of skills from source
get_available_skills() {
    if [ "$INSTALL_FROM_LOCAL" = true ]; then
        # Local: list directories in skills/
        if [ -d "$SCRIPT_DIR/$SKILLS_SOURCE_DIR" ]; then
            for dir in "$SCRIPT_DIR/$SKILLS_SOURCE_DIR"/*/; do
                if [ -f "${dir}SKILL.md" ]; then
                    basename "$dir"
                fi
            done
        fi
    else
        # Remote: fetch skills list from repo
        # This requires a skills-list.txt file or we parse the directory
        # For simplicity, we'll try to download a manifest file
        local manifest=$(curl -sSL -f "${REPO_RAW_URL}/skills/manifest.txt" 2>/dev/null || echo "")
        if [ -n "$manifest" ]; then
            echo "$manifest"
        else
            echo -e "${YELLOW}Warning: Could not fetch remote skills manifest${NC}" >&2
            echo -e "Use --local to install from local skills/ directory" >&2
        fi
    fi
}

# Download a file from remote
download_file() {
    local remote_path="$1"
    local local_path="$2"
    
    # Create parent directory if needed
    mkdir -p "$(dirname "$local_path")"
    
    if curl -sSL -f "${REPO_RAW_URL}/${remote_path}" -o "$local_path" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Install skill to Claude (.claude/skills/)
install_skill_claude() {
    local skill_name="$1"
    local skill_dir="$CLAUDE_SKILLS_DIR/$skill_name"
    
    # Create skill directory
    mkdir -p "$skill_dir"
    
    if [ "$INSTALL_FROM_LOCAL" = true ]; then
        # Copy from local
        local source_dir="$SCRIPT_DIR/$SKILLS_SOURCE_DIR/$skill_name"
        
        if [ ! -f "$source_dir/SKILL.md" ]; then
            echo -e "    ${RED}✗${NC} SKILL.md not found"
            return 1
        fi
        
        # Copy all files from skill directory
        cp -r "$source_dir"/* "$skill_dir/"
        echo -e "    ${GREEN}✓${NC} Installed to $skill_dir/"
    else
        # Download from remote
        if download_file "$SKILLS_SOURCE_DIR/$skill_name/SKILL.md" "$skill_dir/SKILL.md"; then
            echo -e "    ${GREEN}✓${NC} Downloaded SKILL.md"
        else
            echo -e "    ${RED}✗${NC} Failed to download SKILL.md"
            rm -rf "$skill_dir"
            return 1
        fi
        
        # Try to download extra files (listed in manifest or discovered)
        # For now, we just download SKILL.md - extra files can be added later
    fi
    
    return 0
}

# Get Cursor-specific configuration for a skill
# Returns: "alwaysApply|globs"
get_cursor_config() {
    local skill_name="$1"
    
    # Core skills that should always be applied (based on README description)
    # "Test code directly on clusters, then deploy with Databricks Asset Bundles (DABs)"
    case "$skill_name" in
        databricks-testing)
            echo "true|"
            ;;
        databricks-bundle-deploy)
            echo "true|"
            ;;
        databricks-unity-catalog)
            echo "true|"
            ;;
        databricks-ml-pipeline)
            # ML pipeline is contextual - apply when working with ML files
            echo "false|"
            ;;
        databricks-data-engineering)
            # Data engineering is contextual
            echo "false|"
            ;;
        *)
            # Default: not always applied
            echo "false|"
            ;;
    esac
}

# Install skill to Cursor (.cursor/rules/)
install_skill_cursor() {
    local skill_name="$1"
    local output_file="$CURSOR_RULES_DIR/${skill_name}.mdc"
    
    # Create rules directory
    mkdir -p "$CURSOR_RULES_DIR"
    
    local skill_md=""
    local description=""
    
    if [ "$INSTALL_FROM_LOCAL" = true ]; then
        local source_file="$SCRIPT_DIR/$SKILLS_SOURCE_DIR/$skill_name/SKILL.md"
        
        if [ ! -f "$source_file" ]; then
            echo -e "    ${RED}✗${NC} SKILL.md not found"
            return 1
        fi
        
        skill_md="$source_file"
    else
        # Download to temp file
        skill_md=$(mktemp)
        if ! download_file "$SKILLS_SOURCE_DIR/$skill_name/SKILL.md" "$skill_md"; then
            echo -e "    ${RED}✗${NC} Failed to download SKILL.md"
            rm -f "$skill_md"
            return 1
        fi
    fi
    
    # Extract description from Claude format frontmatter
    description=$(extract_frontmatter "description" "$skill_md")
    
    # Default description if not found
    if [ -z "$description" ]; then
        description="Databricks ${skill_name} patterns and best practices"
    fi
    
    # Get Cursor-specific configuration (alwaysApply, globs)
    local cursor_config=$(get_cursor_config "$skill_name")
    local always_apply=$(echo "$cursor_config" | cut -d'|' -f1)
    local globs=$(echo "$cursor_config" | cut -d'|' -f2)
    
    # Create Cursor rule file with Cursor-format frontmatter
    cat > "$output_file" << EOF
---
description: ${description}
globs: ${globs}
alwaysApply: ${always_apply}
---

EOF
    
    # Append skill content (skip original Claude frontmatter)
    awk '
        BEGIN { in_frontmatter=0; frontmatter_done=0 }
        /^---$/ { 
            if (!frontmatter_done) {
                in_frontmatter = !in_frontmatter
                if (!in_frontmatter) frontmatter_done=1
                next
            }
        }
        !in_frontmatter { print }
    ' "$skill_md" >> "$output_file"
    
    # Clean up temp file if remote
    if [ "$INSTALL_FROM_LOCAL" = false ]; then
        rm -f "$skill_md"
    fi
    
    echo -e "    ${GREEN}✓${NC} Created $output_file"
    return 0
}

# ============================================================
# Main Script
# ============================================================

# Parse arguments
while [ $# -gt 0 ]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --list|-l)
            LIST_ONLY=true
            shift
            ;;
        --claude)
            INSTALL_CLAUDE=true
            shift
            ;;
        --cursor)
            INSTALL_CURSOR=true
            shift
            ;;
        --all)
            INSTALL_CLAUDE=true
            INSTALL_CURSOR=true
            shift
            ;;
        --local)
            INSTALL_FROM_LOCAL=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information."
            exit 1
            ;;
    esac
done

# List skills and exit
if [ "$LIST_ONLY" = true ]; then
    echo -e "${BLUE}Available Skills:${NC}"
    echo ""
    
    INSTALL_FROM_LOCAL=true  # List from local by default
    skills=$(get_available_skills)
    
    if [ -z "$skills" ]; then
        echo -e "${YELLOW}No skills found in skills/ directory${NC}"
        exit 0
    fi
    
    for skill in $skills; do
        skill_file="$SCRIPT_DIR/$SKILLS_SOURCE_DIR/$skill/SKILL.md"
        description=$(extract_frontmatter "description" "$skill_file")
        if [ -z "$description" ]; then
            description="(no description)"
        fi
        echo -e "  ${GREEN}$skill${NC}"
        echo -e "    $description"
    done
    echo ""
    exit 0
fi

# Check that at least one target is specified
if [ "$INSTALL_CLAUDE" = false ] && [ "$INSTALL_CURSOR" = false ]; then
    echo -e "${RED}Error: You must specify a target: --claude, --cursor, or --all${NC}"
    echo ""
    show_help
    exit 1
fi

# Header
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           Databricks MCP Skills Installer                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Show what we're installing to
targets=""
[ "$INSTALL_CLAUDE" = true ] && targets="${targets}Claude Code "
[ "$INSTALL_CURSOR" = true ] && targets="${targets}Cursor "
echo -e "${GREEN}Installing to:${NC} ${targets}"

if [ "$INSTALL_FROM_LOCAL" = true ]; then
    echo -e "${BLUE}Source:${NC} Local (${SCRIPT_DIR}/${SKILLS_SOURCE_DIR}/)"
else
    echo -e "${BLUE}Source:${NC} Remote (${REPO_RAW_URL})"
fi
echo ""

# Check if we're in a project directory
if [ ! -d ".git" ] && [ ! -f "pyproject.toml" ] && [ ! -f "package.json" ] && [ ! -f "databricks.yml" ]; then
    echo -e "${YELLOW}Warning: This doesn't look like a project root directory.${NC}"
    echo -e "Current directory: $(pwd)"
    read -p "Continue anyway? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Aborted."
        exit 1
    fi
    echo ""
fi

# Get available skills
skills=$(get_available_skills)

if [ -z "$skills" ]; then
    echo -e "${RED}No skills found!${NC}"
    if [ "$INSTALL_FROM_LOCAL" = true ]; then
        echo "Check that skills/ directory exists with SKILL.md files."
    else
        echo "Could not fetch skills from remote. Try using --local."
    fi
    exit 1
fi

# Count skills
skill_count=$(echo "$skills" | wc -w | tr -d ' ')
echo -e "${GREEN}Found ${skill_count} skill(s) to install${NC}"
echo ""

# Install each skill
claude_installed=0
cursor_installed=0
failed=0

for skill in $skills; do
    echo -e "${BLUE}Installing:${NC} $skill"
    
    if [ "$INSTALL_CLAUDE" = true ]; then
        if install_skill_claude "$skill"; then
            claude_installed=$((claude_installed + 1))
        else
            failed=$((failed + 1))
        fi
    fi
    
    if [ "$INSTALL_CURSOR" = true ]; then
        if install_skill_cursor "$skill"; then
            cursor_installed=$((cursor_installed + 1))
        else
            failed=$((failed + 1))
        fi
    fi
    
    echo ""
done

# Summary
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Installation complete!${NC}"
echo ""

if [ "$INSTALL_CLAUDE" = true ]; then
    echo -e "  Claude Code: ${claude_installed} skill(s) → ${CLAUDE_SKILLS_DIR}/"
fi

if [ "$INSTALL_CURSOR" = true ]; then
    echo -e "  Cursor:      ${cursor_installed} skill(s) → ${CURSOR_RULES_DIR}/"
fi

if [ $failed -gt 0 ]; then
    echo -e "  ${RED}Failed: ${failed}${NC}"
fi

echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Configure .cursor/mcp.json or .claude/mcp.json for the Databricks MCP server"
echo -e "  2. Restart your AI client to pick up the new skills"
echo -e "  3. Start building with Databricks!"
echo ""
