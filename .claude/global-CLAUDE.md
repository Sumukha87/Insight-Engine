# Global User Preferences

## Environment
- OS: Windows 11 with Ubuntu WSL2
- Editor: VS Code with WSL2 remote extension
- Shell: bash (WSL2)
- GPU: RTX 4060 8GB VRAM — available via CUDA in WSL2
- Docker: Docker Desktop with WSL2 backend

## My Defaults
- Always explain what a command does before running it if it modifies files or state
- When writing scripts, add a brief comment block at the top explaining what the script does
- Prefer explicit over implicit — no magic, no hidden behavior
- When I ask "how do I do X", give me the actual command, not just the concept
- If a task requires multiple steps, number them

## Terminal Habits
- I run commands from WSL2 Ubuntu terminal
- Python: always check `which python` returns WSL2 path, not Windows path
- Docker: `docker compose` (v2, with space) not `docker-compose`

## Code Preferences
- I prefer reading small focused functions over long ones
- Add type hints to Python — I find them helpful for understanding
- When generating new files, also tell me where to put them in the project
