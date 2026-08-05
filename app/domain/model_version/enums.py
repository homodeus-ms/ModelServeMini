from enum import Enum

# None : 아직 운영 안됨
# ARCHIVED : 과거에 운영했었음
# PRODUCTION : 현재 운영중, Model당 딱 한개
class DeploymentStatus(str, Enum):
    NONE = "NONE"
    ARCHIVED = "ARCHIVED"
    PRODUCTION = "PRODUCTION"