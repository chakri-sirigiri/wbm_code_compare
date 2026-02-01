# webMethods Integration Server Code Compare

A lightweight tool to **discover, transpose, and analyze** webMethods Integration Server-based assets. This project treats runtime execution as out of scope, focusing on analyzing configuration and state.

> [!NOTE]  
> This project is for **educational purposes only**. It focuses on describing systems, not running them.

## Scenarios

The tool supports two primary workflows:

### 1. Branch vs Branch (Remote Repo)
Compares assets between two branches in a remote Git repository (e.g., `master` vs `develop`).
- **Use Case**: Reviewing changes before merging a feature branch.
- **Output**: Detailed HTML report showing added, removed, and modified packages, services, and properties.

### 2. Branch in Repo vs Local Folder
Compares a specific branch in a remote repo against assets stored in your local filesystem.
- **Use Case**: Verifying local development changes against the current state of a remote environment.
- **Output**: HTML report highlighting discrepancies between local files and the repository.

## Sample Reports

Explore what the tool can do with these live samples:
- [Branch vs Branch Comparison Report](app/reports/sample_report_branch_vs_branch.html)
- [Local Folder vs Repo Branch Report](app/reports/sample_report_branch_vs_local.html)

The tool generates interactive HTML reports in the `app/reports/` directory:

| Report Section | Description |
| :--- | :--- |
| **Metadata** | Shows the scenario, source/target branches or folders, and execution timestamp. |
| **Summary Cards** | High-level counts of Added, Removed, and Modified assets. |
| **Commit Log** | (Scenario 1) Lists commits present in the Head branch but missing from Base. |
| **Asset Differences** | A sortable list of all changed assets with their type and status. |

## Quick Start

### Using Run Scripts
Two pre-configured scripts are provided for a quick start:

```bash
# Compare master vs develop on the sample repo
./run_code_compare_git_branch_vs_branch.sh

# Compare master vs a demo local folder structure
./run_compare_git_branch_vs_local_folder.sh
```

### Interactive Mode
Run without arguments to enter the guided interactive mode:

```bash
uv run python -m src.main
```

## Advanced Usage

For direct CLI control, use the following arguments:

```bash
uv run python -m src.main --scenario [1|2] --repo [URL] --base [BRANCH] [--head BRANCH] [--local-pkgs PATH] [--local-props PATH]
```

## Ethics, Compliance & Disclaimer

- **Static Analysis**: This tool performs offline, read-only static analysis by parsing XML and text-based configuration files. It does not interact with running systems or execute proprietary flow code.
- **Independence**: This project is not affiliated with, endorsed by, or sponsored by IBM or Software AG.
- **Trademarks**: **webMethods** is a trademark of IBM.
- **Compliance**: This project is for **educational purposes only**. Users are responsible for ensuring their use of this tool complies with their respective software license agreements.
- **No Liability**: This software is provided "as is", without warranty of any kind. The author shall not be liable for any claim, damages, or other liability arising from the use of this tool.

## Author
**Chakradhar Sirigiri**

## Credits
Original idea, architecture, and initial implementation by **Chakradhar Sirigiri**.

## License
Apache 2.0
