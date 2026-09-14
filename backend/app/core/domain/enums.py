from enum import StrEnum


class MembershipRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    VIEWER = "viewer"
    ACCOUNTANT = "accountant"
    TAX_ADVISOR = "tax_advisor"
    PAYROLL = "payroll"
    HR = "hr"


class AuditResult(StrEnum):
    SUCCESS = "success"
    DENIED = "denied"
    FAILURE = "failure"
