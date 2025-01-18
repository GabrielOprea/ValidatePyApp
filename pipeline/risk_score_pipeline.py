import csv
import os
import sys
import git
import re
from collections import Counter
import code_features

WEIGHTS = {
    "complexity": 1,
    "frequency": 20,
    "sensitive_data": 30,
    "external_dependencies": 5
}

SENSITIVE_KEYWORDS = ["password", "secret", "token", "api_key", "credential", "token", "api_token", "rest_key", "db_pass", "dbpass", "db_password", "dbpassword"]

scaling_factor = float(os.getenv('SCALING_FACTOR', '0.2'))
complexity_weight = float(os.getenv('COMPLEXITY_WEIGHT', '1'))
external_dependencies_weight = float(os.getenv('EXTERNAL_DEPENDENCIES_WEIGHT', '5'))
fingerprint_threshold = float(os.getenv('FINGERPRINT_THRESHOLD', '0.088'))
frequency_weight = float(os.getenv('FREQUENCY_WEIGHT', '20'))
repo_path_str = os.getenv('REPO_PATH', './repository')
repo_url = os.getenv('REPO_URL', 'https://github.com/GabrielOprea/ValidatePyApp')
risk_threshold = float(os.getenv('RISK_THRESHOLD', '18'))
sensitive_data_weight = float(os.getenv('SENSITIVE_DATA_WEIGHT', '30'))


def clone_repo(repo_url, repo_path):
    if not os.path.exists(repo_path):
        git.Repo.clone_from(repo_url, repo_path)
    return git.Repo(repo_path)

def get_commit_history(repo):
    return list(reversed(list(repo.iter_commits())))

def calculate_complexity_score(total_diff):
    complexity_indicators = ["if", "for", "while", "switch", "try", "catch"]
    return sum(total_diff.count(indicator) for indicator in complexity_indicators)

def calculate_frequency_score(commit_files, all_commit_files):
    file_change_counts = Counter(all_commit_files)
    
    score = 0
    for file in commit_files:
        if file in file_change_counts:
            score += 1 / (file_change_counts[file] + 1)

    return score / len(commit_files) if commit_files else 0

def check_sensitive_data(total_diff):
    return any(keyword in total_diff.lower() for keyword in SENSITIVE_KEYWORDS)

def count_external_dependencies(total_diff):
    dependency_patterns = [
        r"import\s+[a-zA-Z_]+",  # Python
    ]
    
    count = sum(len(re.findall(pattern, total_diff)) for pattern in dependency_patterns)
    return count

def calculate_risk_score(complexity, frequency, sensitive_data, dependencies):
    return (
        complexity_weight * complexity +
        frequency_weight * frequency +
        sensitive_data_weight * sensitive_data +
        external_dependencies_weight * dependencies
    )

def analyze_commits(repo):
    commits = get_commit_history(repo)
    commit_risk_scores = []
    all_commit_files = []
    for commit in commits:
        if '#no_anomaly' in commit.message:
            continue
        files_changed = []

        for diff in commit.diff(commit.parents[0] if commit.parents else None, create_patch=True):
            if diff.a_path and diff.a_path.endswith('.py'):
                files_changed.append({
                    "file_path": diff.a_path,
                    "diff": diff.diff.decode('utf-8', errors='ignore')
                })
                all_commit_files.append(diff.a_path)
        total_diff = code_features.get_total_diff(files_changed)
        complexity_score = calculate_complexity_score(total_diff)
        frequency_score = calculate_frequency_score([file["file_path"] for file in files_changed], all_commit_files)
        sensitive_data_flag = 1 if check_sensitive_data(total_diff) else 0
        dependency_score = count_external_dependencies(total_diff)

        risk_score = calculate_risk_score(complexity_score, frequency_score, sensitive_data_flag, dependency_score)

        commit_risk_scores.append({
            "commit_hash": commit.hexsha,
            "author": commit.author.name,
            "message": commit.message,
            "date": commit.committed_datetime,
            "complexity_score": complexity_score,
            "frequency_score": frequency_score,
            "sensitive_data": sensitive_data_flag,
            "dependency_score": dependency_score,
            "risk_score": risk_score
        })

    return commit_risk_scores

remote_url = repo_url

if __name__ == "__main__":
    repo = clone_repo(remote_url, repo_path_str)
    results = analyze_commits(repo)
    latest_commit_str = list(repo.iter_commits())[0]
    if len(results) == 0 or '#no_anomaly' in latest_commit_str.message:
        sys.exit(0)
    score = results[-1]["risk_score"]
    if score < risk_threshold:
        print(f"Code does not exceed the risk threshold (score: {score})")
        sys.exit(0)
    else:
        print(f"Code exceeds the risk threshold (score: {score})")
        sys.exit(1)