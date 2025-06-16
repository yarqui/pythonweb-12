"""add_user_model_and_link_to_contacts

Revision ID: 7a0b9286105d
Revises: a4d43badfc33
Create Date: 2025-06-13 13:25:21.862914

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7a0b9286105d"
down_revision: Union[str, None] = "a4d43badfc33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TRIGGER_FUNC = """
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';
"""

USERS_UPDATE_TRIGGER = "trigger_users_updated_at"
CONTACTS_UPDATE_TRIGGER = "trigger_contacts_updated_at"


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "users",
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("avatar_url", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.execute(TRIGGER_FUNC)
    op.execute(
        f"""
        CREATE TRIGGER {USERS_UPDATE_TRIGGER}
        BEFORE UPDATE ON users
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """
    )

    op.add_column("contacts", sa.Column("user_id", sa.Integer(), nullable=True))

    op.alter_column("contacts", "user_id", nullable=False)

    op.alter_column(
        "contacts", "email", existing_type=sa.String(length=60), nullable=True
    )
    op.drop_constraint("contacts_email_key", "contacts", type_="unique")

    op.create_unique_constraint(
        "unique_contact_user_email", "contacts", ["user_id", "email"]
    )
    op.create_foreign_key(
        "fk_contacts_users_user_id", "contacts", "users", ["user_id"], ["id"]
    )

    op.alter_column("contacts", "created_at", server_default=None)
    op.alter_column("contacts", "updated_at", server_default=None)
    op.execute(
        f"""
        CREATE TRIGGER {CONTACTS_UPDATE_TRIGGER}
        BEFORE UPDATE ON contacts
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""

    op.execute(f"DROP TRIGGER IF EXISTS {CONTACTS_UPDATE_TRIGGER} ON contacts;")
    op.drop_constraint("fk_contacts_users_user_id", "contacts", type_="foreignkey")
    op.drop_constraint("unique_contact_user_email", "contacts", type_="unique")
    op.create_unique_constraint("contacts_email_key", "contacts", ["email"])
    op.alter_column(
        "contacts", "email", existing_type=sa.String(length=60), nullable=False
    )
    op.drop_column("contacts", "user_id")
    op.alter_column("contacts", "updated_at", server_default=sa.text("now()"))
    op.alter_column("contacts", "created_at", server_default=sa.text("now()"))

    op.execute(f"DROP TRIGGER IF EXISTS {USERS_UPDATE_TRIGGER} ON users;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    # ### end Alembic commands ###
