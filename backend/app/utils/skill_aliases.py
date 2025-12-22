"""
Skill normalization utilities.

Maps common skill variations to canonical names for consistent matching.
"""

# Mapping of lowercase variations -> canonical display name
SKILL_ALIASES = {
    # JavaScript ecosystem
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "reactjs": "React",
    "react.js": "React",
    "react js": "React",
    "react": "React",
    "vuejs": "Vue",
    "vue.js": "Vue",
    "vue js": "Vue",
    "vue": "Vue",
    "angularjs": "Angular",
    "angular.js": "Angular",
    "angular": "Angular",
    "nodejs": "Node.js",
    "node": "Node.js",
    "node.js": "Node.js",
    "nextjs": "Next.js",
    "next.js": "Next.js",
    "next": "Next.js",
    "expressjs": "Express",
    "express.js": "Express",
    "express": "Express",
    "nestjs": "NestJS",
    "nest.js": "NestJS",
    "nest": "NestJS",

    # Python ecosystem
    "py": "Python",
    "python": "Python",
    "python3": "Python",
    "python 3": "Python",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "fast api": "FastAPI",

    # Databases
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "pg": "PostgreSQL",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "mysql": "MySQL",
    "my sql": "MySQL",
    "mssql": "SQL Server",
    "ms sql": "SQL Server",
    "sql server": "SQL Server",
    "sqlserver": "SQL Server",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch",
    "elastic search": "Elasticsearch",
    "elastic": "Elasticsearch",
    "dynamodb": "DynamoDB",
    "dynamo db": "DynamoDB",
    "dynamo": "DynamoDB",

    # Cloud providers
    "aws": "AWS",
    "amazon web services": "AWS",
    "gcp": "Google Cloud",
    "google cloud platform": "Google Cloud",
    "google cloud": "Google Cloud",
    "azure": "Azure",
    "microsoft azure": "Azure",
    "ms azure": "Azure",

    # DevOps & Infrastructure
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "kube": "Kubernetes",
    "tf": "Terraform",
    "terraform": "Terraform",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "ci cd": "CI/CD",
    "docker": "Docker",
    "ansible": "Ansible",
    "jenkins": "Jenkins",
    "github actions": "GitHub Actions",
    "gh actions": "GitHub Actions",
    "gitlab ci": "GitLab CI",

    # Programming languages
    "cpp": "C++",
    "c++": "C++",
    "cplusplus": "C++",
    "csharp": "C#",
    "c#": "C#",
    "c sharp": "C#",
    "golang": "Go",
    "go": "Go",
    "rust": "Rust",
    "java": "Java",
    "kotlin": "Kotlin",
    "swift": "Swift",
    "ruby": "Ruby",
    "php": "PHP",
    "scala": "Scala",
    "r": "R",

    # Frontend
    "html": "HTML",
    "html5": "HTML",
    "css": "CSS",
    "css3": "CSS",
    "sass": "Sass",
    "scss": "Sass",
    "less": "Less",
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
    "tailwind css": "Tailwind CSS",
    "bootstrap": "Bootstrap",

    # Mobile
    "react native": "React Native",
    "reactnative": "React Native",
    "rn": "React Native",
    "flutter": "Flutter",
    "ios": "iOS",
    "android": "Android",

    # Data & ML
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "ai": "AI",
    "artificial intelligence": "AI",
    "dl": "Deep Learning",
    "deep learning": "Deep Learning",
    "tensorflow": "TensorFlow",
    "tf": "TensorFlow",  # Note: Also maps to Terraform - context dependent
    "pytorch": "PyTorch",
    "torch": "PyTorch",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "scipy": "SciPy",

    # APIs & Protocols
    "rest": "REST",
    "restful": "REST",
    "rest api": "REST",
    "graphql": "GraphQL",
    "grpc": "gRPC",
    "websocket": "WebSocket",
    "websockets": "WebSocket",

    # Testing
    "jest": "Jest",
    "pytest": "pytest",
    "py test": "pytest",
    "unittest": "unittest",
    "mocha": "Mocha",
    "cypress": "Cypress",
    "selenium": "Selenium",

    # Version control
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "bitbucket": "Bitbucket",

    # Messaging & Queues
    "kafka": "Kafka",
    "rabbitmq": "RabbitMQ",
    "rabbit mq": "RabbitMQ",
    "sqs": "SQS",
    "sns": "SNS",

    # Monitoring & Observability
    "datadog": "Datadog",
    "prometheus": "Prometheus",
    "grafana": "Grafana",
    "elk": "ELK Stack",
    "elk stack": "ELK Stack",
    "splunk": "Splunk",
    "newrelic": "New Relic",
    "new relic": "New Relic",
}


def normalize_skill(skill: str) -> str:
    """
    Normalize a skill name for comparison.

    - Strips whitespace
    - Looks up canonical name from aliases
    - Returns canonical name if found, otherwise returns original with preserved case

    Examples:
        normalize_skill("  JS  ") -> "JavaScript"
        normalize_skill("postgres") -> "PostgreSQL"
        normalize_skill("Some Unknown Skill") -> "Some Unknown Skill"
    """
    stripped = skill.strip()
    lookup_key = stripped.lower()

    # Return canonical name if found in aliases, otherwise return original
    return SKILL_ALIASES.get(lookup_key, stripped)


def get_canonical_skill(skill: str) -> str:
    """
    Get the canonical name for a skill (alias for normalize_skill).
    """
    return normalize_skill(skill)
