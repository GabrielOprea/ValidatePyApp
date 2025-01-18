import pickle
import sys

import numpy as np
import git
import os
import shutil
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import code_features

vectorizer = TfidfVectorizer()

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
    """
    Extract commit metadata and modified file content.
    """
    repo = git.Repo(repo_path)
    commit_data = []
    
    for commit in list(repo.iter_commits(rev='HEAD'))[::-1]:
        if '#no_anomaly' not in commit.message:
            files_changed = []
            for diff in commit.diff(commit.parents[0] if commit.parents else None, create_patch=True):
                if diff.a_path and diff.a_path.endswith('.py'):  # Only analyze .py files
                    files_changed.append({
                        "file_path": diff.a_path,
                        "diff": diff.diff.decode('utf-8', errors='ignore')  # Unified diff as a string
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
        if diff.a_path and diff.a_path.endswith('.py'):  # Only analyze .py files
            files_changed.append({
                "file_path": diff.a_path,
                "diff": diff.diff.decode('utf-8', errors='ignore')  # Unified diff as a string
            })
    
    return {
        "author": commit.author.name,
        "message": commit.message,
        "date": commit.committed_date,
        "files_changed": files_changed
    }

def fit_vectorizer(commit_data):
    """
    Fit a single TfidfVectorizer on all commit messages.
    """
    messages = [commit["message"] for commit in commit_data]
    vectorizer = TfidfVectorizer()
    vectorizer.fit(messages)  # Fit on all messages
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
            exit(1)  # Fail the pipeline
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

# def generate_fingerprint(messages, vectorizer):
#     """
#     Transform commit messages into a TF-IDF fingerprint using a shared vectorizer.
#     """
#     tfidf_matrix = vectorizer.transform(messages)
#     return {"tdidf_vectors": tfidf_matrix}

def generate_fingerprint(commit, vectorizer):
    """
    Transform commit messages and additional features into a combined feature vector.
    """
    tfidf_vector = vectorizer.transform([commit["message"]]).toarray()[0]  # TF-IDF for the message
    features = code_features.calculate_features(commit)  # Additional features like avg_nesting_depth
    combined_vector = np.append(tfidf_vector, features["avg_nesting_depth"])  # Combine features
    return combined_vector

def detect_anomalies(old_fingerprint, new_fingerprint):
    similarity = cosine_similarity([old_fingerprint], [new_fingerprint])[0][0]
    print(f"Avg Similarity: {similarity}")
    return similarity < 0.055

def get_anomaly_score(old_fingerprint, new_fingerprint):
    similarity = cosine_similarity([old_fingerprint], [new_fingerprint])[0][0]
    return similarity

remote_url = "https://github.com/GabrielOprea/ValidatePyApp"
local_path = "./pipeline/repository"
old_fingerprint_path = "./stored_fingerprint.pkl"
new_fingerprint_path = "./stored_new.pkl"
repo = clone_repository(remote_url, local_path)
commit_data = get_commit_data(local_path)
# print(commit_data)
# # shutil.rmtree(local_path)
# new_fingerprint = generate_fingerprint(commit_data)
# old_fingerprint = load_old_fingerprint(old_fingerprint_path)
# check_fingerprints(old_fingerprint_path, old_fingerprint, new_fingerprint)

# Fit a single vectorizer on all commit messages
vectorizer = fit_vectorizer(commit_data)
cumulative_fingerprint = None
anomalous_commits = []

latest_commit = commit_data[-1]
if '#no_anomaly' in latest_commit['message']:
    print("Not running anomaly pipeline for this commit (marked with #no_anomaly)")
    sys.exit(0)

for i, commit in enumerate(commit_data[:-1]):
    new_fingerprint = generate_fingerprint(commit, vectorizer)

    # Skip anomaly detection for the first commit
    if cumulative_fingerprint is None:
        cumulative_fingerprint = new_fingerprint
        print("Skipping anomaly detection for the first commit.")
        continue

    cumulative_fingerprint = np.mean([cumulative_fingerprint, new_fingerprint], axis=0)

new_fingerprint = generate_fingerprint(latest_commit, vectorizer)
anomaly = get_anomaly_score(cumulative_fingerprint, new_fingerprint)
if detect_anomalies(cumulative_fingerprint, new_fingerprint):
    print(f"Anomaly detected in commit {latest_commit['hash']}: {latest_commit['message']} ({anomaly})")
    sys.exit(1)
else:
    print(f"No anomaly detected in commit {latest_commit['hash']}: {latest_commit['message']} ({anomaly})")
    sys.exit(0)