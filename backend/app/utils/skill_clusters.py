"""
Skill clusters for semantic skill matching.

Skills in the same cluster are considered related, allowing partial credit
when a user has related but not exact skills.
"""
from typing import Set
from app.utils.skill_aliases import normalize_skill


# Skill clusters - skills in the same cluster are related
# Uses canonical skill names (from skill_aliases.py)
SKILL_CLUSTERS = {
    # Python ecosystem
    "python_web": {"Python", "Django", "Flask", "FastAPI", "SQLAlchemy", "Celery"},
    "python_data": {"Python", "Pandas", "NumPy", "SciPy", "Jupyter"},

    # JavaScript/TypeScript ecosystem
    "javascript_core": {"JavaScript", "TypeScript"},
    "javascript_frontend": {"JavaScript", "TypeScript", "React", "Vue", "Angular", "Next.js", "Svelte"},
    "javascript_backend": {"JavaScript", "TypeScript", "Node.js", "Express", "NestJS", "Fastify"},
    "javascript_mobile": {"JavaScript", "TypeScript", "React Native"},

    # Mobile development
    "mobile_cross": {"React Native", "Flutter", "Ionic"},
    "mobile_ios": {"Swift", "iOS", "Objective-C", "SwiftUI"},
    "mobile_android": {"Kotlin", "Android", "Java"},

    # Databases - SQL
    "databases_sql": {"PostgreSQL", "MySQL", "SQL Server", "SQL", "SQLite", "MariaDB"},
    # Databases - NoSQL
    "databases_nosql": {"MongoDB", "Redis", "Elasticsearch", "DynamoDB", "Cassandra", "CouchDB"},
    # Databases - general
    "databases_orm": {"SQLAlchemy", "Prisma", "TypeORM", "Sequelize", "Django"},

    # Cloud - AWS
    "cloud_aws": {"AWS", "EC2", "S3", "Lambda", "CloudFormation", "ECS", "EKS", "RDS", "DynamoDB"},
    # Cloud - GCP
    "cloud_gcp": {"Google Cloud", "BigQuery", "Cloud Run", "GKE", "Cloud Functions", "Pub/Sub"},
    # Cloud - Azure
    "cloud_azure": {"Azure", "Azure DevOps", "Azure Functions", "AKS"},
    # Cloud - general
    "cloud_general": {"AWS", "Google Cloud", "Azure", "Terraform", "CloudFormation"},

    # DevOps & Infrastructure
    "devops_containers": {"Docker", "Kubernetes", "ECS", "EKS", "GKE", "AKS", "Podman"},
    "devops_iac": {"Terraform", "Ansible", "CloudFormation", "Pulumi", "Chef", "Puppet"},
    "devops_cicd": {"CI/CD", "Jenkins", "GitHub Actions", "GitLab CI", "CircleCI", "Travis CI"},
    "devops_monitoring": {"Prometheus", "Grafana", "Datadog", "New Relic", "ELK Stack", "Splunk"},

    # Machine Learning & AI
    "ml_frameworks": {"TensorFlow", "PyTorch", "scikit-learn", "Keras", "JAX"},
    "ml_tools": {"Python", "Pandas", "NumPy", "Jupyter", "scikit-learn"},
    "ml_ops": {"MLflow", "Kubeflow", "SageMaker", "Vertex AI"},

    # Data Engineering
    "data_processing": {"Apache Spark", "Apache Kafka", "Apache Airflow", "dbt", "Flink"},
    "data_warehousing": {"Snowflake", "BigQuery", "Redshift", "Databricks"},

    # Frontend styling
    "frontend_css": {"CSS", "Sass", "Less", "Tailwind CSS", "Bootstrap", "Styled Components"},

    # Testing
    "testing_js": {"Jest", "Mocha", "Cypress", "Playwright", "Testing Library"},
    "testing_python": {"pytest", "unittest", "Selenium"},

    # API & Protocols
    "api_styles": {"REST", "GraphQL", "gRPC", "WebSocket"},

    # Version Control
    "version_control": {"Git", "GitHub", "GitLab", "Bitbucket"},

    # Backend languages (general similarity)
    "backend_languages": {"Python", "Java", "Go", "Ruby", "PHP", "C#", "Rust"},
}


def get_skill_clusters(skill: str) -> Set[str]:
    """
    Get all cluster names that contain the given skill.

    Args:
        skill: Skill name (will be normalized)

    Returns:
        Set of cluster names containing this skill
    """
    normalized = normalize_skill(skill)
    clusters = set()

    for cluster_name, skills in SKILL_CLUSTERS.items():
        if normalized in skills:
            clusters.add(cluster_name)

    return clusters


def get_related_skills(skill: str) -> Set[str]:
    """
    Get all skills related to the given skill (in same clusters).

    Args:
        skill: Skill name (will be normalized)

    Returns:
        Set of related skill names (excluding the input skill)
    """
    normalized = normalize_skill(skill)
    related = set()

    for cluster_name, skills in SKILL_CLUSTERS.items():
        if normalized in skills:
            related.update(skills)

    # Remove the original skill
    related.discard(normalized)

    return related


def are_skills_related(skill1: str, skill2: str) -> bool:
    """
    Check if two skills are in the same cluster.

    Args:
        skill1: First skill name
        skill2: Second skill name

    Returns:
        True if skills share at least one cluster
    """
    norm1 = normalize_skill(skill1)
    norm2 = normalize_skill(skill2)

    if norm1 == norm2:
        return True

    clusters1 = get_skill_clusters(norm1)
    clusters2 = get_skill_clusters(norm2)

    return bool(clusters1 & clusters2)


def calculate_skill_similarity(user_skill: str, required_skill: str) -> float:
    """
    Calculate similarity score between two skills.

    Args:
        user_skill: Skill the user has
        required_skill: Skill the job requires

    Returns:
        Score: 1.0 = exact match, 0.5 = related (same cluster), 0.0 = unrelated
    """
    user_norm = normalize_skill(user_skill)
    required_norm = normalize_skill(required_skill)

    # Exact match
    if user_norm == required_norm:
        return 1.0

    # Check if related
    if are_skills_related(user_norm, required_norm):
        return 0.5

    return 0.0
