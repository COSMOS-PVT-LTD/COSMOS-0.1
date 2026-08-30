/**
 * COSMOS 0.1 — centralized role-based access policy (frontend).
 * Backend enforcement remains authoritative in api/authorization.py and knowledge/workspace/access.py.
 */
(function rbacModule() {
  const ROLE = (user) => String(user?.role || "").toUpperCase();

  COSMOS.permissions = {
    canAdmin(user) {
      return ROLE(user) === "ADMIN";
    },
    canAudit(user) {
      return ROLE(user) === "ADMIN";
    },
    canKnowledgeAdmin(user) {
      return ROLE(user) === "ADMIN";
    },
    canKnowledgeChat(user) {
      return ["VIEWER", "ENGINEER", "REVIEWER", "APPROVER", "ADMIN"].includes(ROLE(user));
    },
    canKnowledgeGraph(user) {
      return this.canKnowledgeChat(user);
    },
    canRegisterUsers(user) {
      return this.canAdmin(user);
    },
  };

  COSMOS.canAdmin = (user) => COSMOS.permissions.canAdmin(user || COSMOS.currentUser);
  COSMOS.canAudit = (user) => COSMOS.permissions.canAudit(user || COSMOS.currentUser);
  COSMOS.canKnowledgeAdmin = (user) => COSMOS.permissions.canKnowledgeAdmin(user || COSMOS.currentUser);
})();
