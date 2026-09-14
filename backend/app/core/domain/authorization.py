from app.core.domain.enums import MembershipRole

PERMISSIONS: dict[str, str] = {
    "apps.read": "View enabled applications",
    "apps.manage": "Enable or disable applications",
    "members.read": "View organization memberships",
    "members.manage": "Manage organization memberships",
    "roles.manage": "Manage roles and permission grants",
    "audit.read": "View audit events",
    "features.read": "View feature flags",
    "features.manage": "Manage feature flags",
    "commercial.read": "View commercial CRM records",
    "commercial.write": "Create and update commercial CRM records",
}

ROLE_PERMISSIONS: dict[MembershipRole, frozenset[str]] = {
    MembershipRole.OWNER: frozenset(PERMISSIONS),
    MembershipRole.ADMIN: frozenset(PERMISSIONS),
    MembershipRole.MANAGER: frozenset(
        {
            "apps.read",
            "members.read",
            "audit.read",
            "features.read",
            "commercial.read",
            "commercial.write",
        }
    ),
    MembershipRole.EMPLOYEE: frozenset({"apps.read", "commercial.read", "commercial.write"}),
    MembershipRole.VIEWER: frozenset({"apps.read", "features.read", "commercial.read"}),
    MembershipRole.ACCOUNTANT: frozenset({"apps.read"}),
    MembershipRole.TAX_ADVISOR: frozenset({"apps.read"}),
    MembershipRole.PAYROLL: frozenset({"apps.read"}),
    MembershipRole.HR: frozenset({"apps.read", "members.read"}),
}

APPLICATIONS: dict[str, str] = {
    "core": "ProcessOS Core",
    "commercial": "Commercial OS",
    "audit": "ProcessOS Audit",
    "time": "ProcessOS Time",
    "docs": "ProcessOS Docs",
    "finance": "ProcessOS Finance",
    "tax": "ProcessOS Tax",
    "hr": "ProcessOS HR",
    "payroll": "ProcessOS Payroll",
}
