"""
Repositories — data-access layer. SQL/ORM lives here, nowhere else.

One repository per aggregate (StudyRepo, MappingRepo, AuditRepo, ...).
Services call repositories; routers never touch the DB directly.
Repositories must NOT import the engine (boundary rule).

Added during Sprint 2 as the persistence layer lands.
"""
