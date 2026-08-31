import uuid

from app.repositories.organization_repository import OrganizationRepository


async def test_create_and_get_by_id_round_trip(pg_connection):
    repo = OrganizationRepository()
    code = f"ORG_{uuid.uuid4().hex[:8]}"

    created = await repo.create("Test Organization", code, description="integration test", connection=pg_connection)
    assert created["code"] == code
    assert created["active"] is True

    fetched = await repo.get_by_id(created["organization_id"], connection=pg_connection)
    assert fetched is not None
    assert fetched["organization_id"] == created["organization_id"]
    assert fetched["name"] == "Test Organization"


async def test_get_by_code(pg_connection):
    repo = OrganizationRepository()
    code = f"ORG_{uuid.uuid4().hex[:8]}"
    await repo.create("Another Org", code, connection=pg_connection)

    fetched = await repo.get_by_code(code, connection=pg_connection)
    assert fetched is not None
    assert fetched["code"] == code


async def test_get_by_id_returns_none_for_unknown_id(pg_connection):
    repo = OrganizationRepository()
    result = await repo.get_by_id(str(uuid.uuid4()), connection=pg_connection)
    assert result is None


async def test_list_all_excludes_inactive_by_default(pg_connection):
    repo = OrganizationRepository()
    code = f"ORG_{uuid.uuid4().hex[:8]}"
    created = await repo.create("Inactive Org", code, connection=pg_connection)
    await pg_connection.execute(
        "UPDATE organizations SET active = FALSE WHERE organization_id = $1", created["organization_id"]
    )

    active_orgs = await repo.list_all(active_only=True, connection=pg_connection)
    assert all(o["organization_id"] != created["organization_id"] for o in active_orgs)

    all_orgs = await repo.list_all(active_only=False, connection=pg_connection)
    assert any(o["organization_id"] == created["organization_id"] for o in all_orgs)
