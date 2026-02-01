import argparse
import sys
from pathlib import Path

from src.analysis.comparer import CodeComparator
from src.models.assets.webmethods import discover_all_assets, flatten_assets
from src.models.git_repo import GitRepo
from src.utils.logger import setup_logger

logger = setup_logger("ibm_wbm_code_compare")


def get_input(prompt: str, default: str | None = None) -> str:
    """Helper to get user input with an optional default value."""
    if default:
        val = input(f"{prompt} [{default}]: ").strip()
        return val if val else default

    while True:
        val = input(f"{prompt}: ").strip()
        if val:
            return val
        print("Input required.")


def run_branch_vs_branch(repo_url: str, base_branch: str, head_branch: str, workdir: str):
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    local_path = Path(workdir) / repo_name
    repo = GitRepo(remote_url=repo_url, local_path=local_path)

    if not repo.clone_or_pull():
        logger.error("Failed to prepare repository.")
        return

    # 1. Base Assets
    if not repo.checkout(base_branch):
        logger.error(f"Failed to checkout base: {base_branch}")
        return
    logger.info(f"Scanning base branch: {base_branch}")
    base_assets = flatten_assets(discover_all_assets(local_path))

    # 2. Head Assets
    if not repo.checkout(head_branch):
        logger.error(f"Failed to checkout head: {head_branch}")
        return
    logger.info(f"Scanning head branch: {head_branch}")
    head_assets = flatten_assets(discover_all_assets(local_path))

    # 3. Compare & Report
    comparator = CodeComparator()
    result = comparator.compare_assets(base_assets, head_assets)
    commits = repo.get_commit_log(base_branch, head_branch)

    info = {
        "scenario": "Branch vs Branch",
        "repo_url": repo_url,
        "repo_name": repo_name,
        "base_branch": base_branch,
        "head_branch": head_branch,
        "source_label": "Base (Source)",
        "target_label": "Compare (Target)",
    }
    report_file = comparator.generate_html_report(result, info, commits)
    print_summary(result, report_file)


def run_branch_vs_local(
    repo_url: str,
    branch: str,
    local_packages: str | None,
    local_properties: str | None,
    workdir: str,
):
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    repo_local_path = Path(workdir) / repo_name
    repo = GitRepo(remote_url=repo_url, local_path=repo_local_path)

    if not repo.clone_or_pull():
        logger.error("Failed to prepare repository.")
        return

    # 1. Repo Assets (Source)
    if not repo.checkout(branch):
        logger.error(f"Failed to checkout branch: {branch}")
        return
    logger.info(f"Scanning repo branch: {branch}")
    repo_assets = flatten_assets(discover_all_assets(repo_local_path))

    # 2. Local Assets (Target)
    logger.info("Scanning local folders...")
    local_assets = []
    if local_packages:
        from src.models.assets.webmethods import discover_packages

        local_assets.extend(discover_packages(Path(local_packages).expanduser().resolve()))
    if local_properties:
        from src.models.assets.webmethods import discover_properties

        local_assets.extend(discover_properties(Path(local_properties).expanduser().resolve()))

    head_assets = flatten_assets(local_assets)
    logger.info(f"Total head assets for comparison: {len(head_assets)}")

    # 3. Compare & Report
    comparator = CodeComparator()
    result = comparator.compare_assets(repo_assets, head_assets)

    # Commits are relative to repo branches, not applicable here between repo and local
    info = {
        "scenario": "Branch in Repo vs Local Folder",
        "repo_url": repo_url,
        "repo_name": repo_name,
        "base_branch": branch,
        "head_branch": "Local Folders",
        "source_label": "Repo (Source)",
        "target_label": "Local (Target)",
        "source_extra": f"on {repo_name}",
        "target_extra": "",
        "local_packages": local_packages,
        "local_properties": local_properties,
    }
    report_file = comparator.generate_html_report(result, info)
    print_summary(result, report_file)


def print_summary(result, report_file):
    logger.info("=" * 40)
    logger.info("Comparison Complete!")
    logger.info(f"Added: {len(result.added)}")
    logger.info(f"Removed: {len(result.removed)}")
    logger.info(f"Modified: {len(result.modified)}")
    logger.info(f"Report: {report_file}")
    logger.info("=" * 40)


def main():
    parser = argparse.ArgumentParser(description="webMethods Branch Comparator")
    parser.add_argument(
        "--scenario",
        type=int,
        choices=[1, 2],
        help="1: Branch vs Branch, 2: Branch vs Local",
    )
    parser.add_argument("--repo", help="Git Repository URL")
    parser.add_argument("--base", help="Base/Repo branch")
    parser.add_argument("--head", help="Head branch (Scenario 1)")
    parser.add_argument("--local-pkgs", help="Local Packages folder (Scenario 2)")
    parser.add_argument("--local-props", help="Local Properties folder (Scenario 2)")
    parser.add_argument("--workdir", default="./tmp/repos", help="Working directory")

    args = parser.parse_args()

    scenario = args.scenario
    if not scenario:
        print("\nSelect Scenario:")
        print("1. Branch vs Branch (Remote Repo)")
        print("2. Branch in Repo vs Local Folder")
        s_input = input("\nEnter choice [1-2]: ").strip()
        scenario = int(s_input) if s_input in ["1", "2"] else 1

    if scenario == 1:
        repo = args.repo or get_input("Git Repository URL")
        base = args.base or get_input("Base branch", "main")
        head = args.head or get_input("Head branch")
        run_branch_vs_branch(repo, base, head, args.workdir)
    else:
        repo = args.repo or get_input("Git Repository URL")
        branch = args.base or get_input("Repo branch", "main")

        pkgs = args.local_pkgs
        props = args.local_props

        if not pkgs and not props:
            print("\nProvide at least one local folder path:")
            pkgs = input("Local Packages folder [skip]: ").strip() or None
            props = input("Local Properties folder [skip]: ").strip() or None

            if not pkgs and not props:
                logger.error(
                    "At least one target folder (Packages or Properties) must be provided."
                )
                sys.exit(1)

        run_branch_vs_local(repo, branch, pkgs, props, args.workdir)


if __name__ == "__main__":
    main()
