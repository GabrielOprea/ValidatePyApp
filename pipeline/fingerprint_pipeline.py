import pickle
import sys
from sklearn.preprocessing import StandardScaler

import numpy as np
import git
import os
import shutil
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import code_features

vectorizer = TfidfVectorizer()
scaling_factor = float(os.getenv('SCALING_FACTOR', '0.2'))
complexity_weight = float(os.getenv('COMPLEXITY_WEIGHT', '1'))
external_dependencies_weight = float(os.getenv('EXTERNAL_DEPENDENCIES_WEIGHT', '5'))
fingerprint_threshold = float(os.getenv('FINGERPRINT_THRESHOLD', '0.088'))
frequency_weight = float(os.getenv('FREQUENCY_WEIGHT', '20'))
repo_path = os.getenv('REPO_PATH', './repository')
repo_url = os.getenv('REPO_URL', 'https://github.com/GabrielOprea/ValidatePyApp')
risk_threshold = float(os.getenv('RISK_THRESHOLD', '18'))
sensitive_data_weight = float(os.getenv('SENSITIVE_DATA_WEIGHT', '30'))

def clone_repository(remote_url, local_path):
    if not os.path.exists(local_path):
        print(f"Cloning repository from {remote_url} to {local_path}...")
        repo = git.Repo.clone_from(remote_url, local_path)
        print("Repository cloned successfully.")
    else:
        print(f"Repository already exists at {local_path}.")
        repo = git.Repo(local_path)
    return repo

def get_commit_data(repo_path):
    repo = git.Repo(repo_path)
    commit_data = []
    
    for commit in list(repo.iter_commits(rev='HEAD'))[::-1]:
        if '#no_anomaly' not in commit.message:
            files_changed = []
            for diff in commit.diff(commit.parents[0] if commit.parents else None, create_patch=True):
                if diff.a_path and diff.a_path.endswith('.py'):
                    files_changed.append({
                        "file_path": diff.a_path,
                        "diff": diff.diff.decode('utf-8', errors='ignore')
                    })
                
            commit_data.append({
                "hash": commit.hexsha,
                "author": commit.author.name,
                "message": commit.message,
                "date": commit.committed_date,
                "files_changed": files_changed
            })
    return commit_data

def get_commit_data_for_commit(repo, commit):
    files_changed = []
    for diff in commit.diff(commit.parents[0] if commit.parents else None, create_patch=True):
        if diff.a_path and diff.a_path.endswith('.py'):
            files_changed.append({
                "file_path": diff.a_path,
                "diff": diff.diff.decode('utf-8', errors='ignore')
            })
    
    return {
        "author": commit.author.name,
        "message": commit.message,
        "date": commit.committed_date,
        "files_changed": files_changed
    }

def fit_vectorizer(commit_data):
    messages = [commit["message"] for commit in commit_data]
    vectorizer = TfidfVectorizer()
    vectorizer.fit(messages)
    return vectorizer

def load_old_fingerprint(old_fingerprint_path):
    if os.path.exists(old_fingerprint_path):
        import pickle
        with open(old_fingerprint_path, "rb") as f:
            old_fingerprint = pickle.load(f)
    else:
        old_fingerprint = None
    return old_fingerprint

def check_fingerprints(old_fingerprint_path, old_fingerprint, new_fingerprint):
    if old_fingerprint:
        if detect_anomalies(old_fingerprint, new_fingerprint):
            print("Anomaly detected in the commit fingerprint.")
            exit(1)
        else:
            print("No anomalies detected.")
    else:
        print("No stored fingerprint found. Storing the current fingerprint.")
        with open(old_fingerprint_path, "wb") as f:
            pickle.dump(new_fingerprint, f)

def generate_fingerprint(commit_data):
    messages = [commit["message"] for commit in commit_data]
    tfidf_matrix = vectorizer.fit_transform(messages)
    return {"tdidf_vectors": tfidf_matrix}

def generate_fingerprint(commit, vectorizer):
    tfidf_vector = vectorizer.transform([commit["message"]]).toarray()[0]
    features = code_features.calculate_features(commit)

    feature_min = np.array([0, 0, 0, 0])
    feature_max = np.array([6, 21, 1, 1])

    feature_values = np.array([
        features["avg_nesting_depth"],
        features["avg_indentation"],
        features["snake_case_ratio"],
        features["camel_case_ratio"]
    ])

    normalized_features = scaling_factor * (feature_values - feature_min) / (feature_max - feature_min)

    combined_vector = np.append(tfidf_vector, normalized_features)
    return combined_vector

def detect_anomalies(old_fingerprint, new_fingerprint):
    similarity = cosine_similarity([old_fingerprint], [new_fingerprint])[0][0]
    return similarity < fingerprint_threshold

def get_anomaly_score(old_fingerprint, new_fingerprint):
    similarity = cosine_similarity([old_fingerprint], [new_fingerprint])[0][0]
    return similarity

def get_anomaly_score(old_fingerprint, new_fingerprint):
    similarity = cosine_similarity([old_fingerprint], [new_fingerprint])[0][0]

    return similarity

remote_url = repo_url
local_path = repo_path
repo = clone_repository(remote_url, local_path)
commit_data = get_commit_data(local_path)

latest_commy = list(repo.iter_commits(rev='HEAD'))[0]
if '#no_anomaly' in latest_commy.message:
    sys.exit(0)

vectorizer = fit_vectorizer(commit_data)
cumulative_fingerprint = None
anomalous_commits = []

is_anomalous = False
latest_commit = commit_data[-1]
if '#no_anomaly' in latest_commit["message"]:
    sys.exit(0)
for i, commit in enumerate(commit_data[:-1]):
    new_fingerprint = generate_fingerprint(commit, vectorizer)

    if cumulative_fingerprint is None:
        cumulative_fingerprint = new_fingerprint
        continue

    cumulative_fingerprint = np.mean([cumulative_fingerprint, new_fingerprint], axis=0)

new_fingerprint = generate_fingerprint(latest_commit, vectorizer)
score = get_anomaly_score(cumulative_fingerprint, new_fingerprint)
if detect_anomalies(cumulative_fingerprint, new_fingerprint):
    print(f"Anomaly detected in commit {latest_commit['hash']}: {latest_commit['message']} ({score})")
    sys.exit(1)
else:
    print(f"No anomaly detect in commit  {latest_commit['hash']}: {latest_commit['message']} ({score})")
    sys.exit(0)