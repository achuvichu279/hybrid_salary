import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder
import joblib

# Load dataset
df = pd.read_csv("finance_data.csv")

# Encode district
encoder = LabelEncoder()
df['district_encoded'] = encoder.fit_transform(df['district'])

# -----------------------------
# SUPERVISED LEARNING
# -----------------------------
X = df[['salary', 'family_members', 'district_encoded']]
y = df['expense']

model = LinearRegression()
model.fit(X, y)

joblib.dump(model, "models/expense_model.pkl")

# -----------------------------
# UNSUPERVISED LEARNING
# -----------------------------
cluster_data = df[['salary', 'expense', 'savings']]

kmeans = KMeans(n_clusters=3, random_state=42)
kmeans.fit(cluster_data)

joblib.dump(kmeans, "models/savings_cluster.pkl")

# Save encoder
joblib.dump(encoder, "models/encoder.pkl")

print("Models trained successfully")