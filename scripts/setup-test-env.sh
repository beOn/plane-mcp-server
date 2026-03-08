#!/usr/bin/env bash
# Start the ephemeral test Plane stack, wait for readiness, seed test data.
#
# Exports: PLANE_BASE_URL, PLANE_API_KEY, PLANE_WORKSPACE_SLUG
# Usage:  eval "$(./scripts/setup-test-env.sh)"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

COMPOSE="docker compose -f docker-compose-test.yml"

echo "==> Starting ephemeral test stack..." >&2
$COMPOSE up -d --build 2>&1 | tail -5 >&2

# Wait for migrator to finish
echo "==> Waiting for migrations..." >&2
for i in $(seq 1 60); do
    status=$($COMPOSE ps --format json test-migrator 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('State',''))" 2>/dev/null || echo "unknown")
    if [ "$status" = "exited" ]; then
        exit_code=$($COMPOSE ps --format json test-migrator 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('ExitCode',1))" 2>/dev/null || echo "1")
        if [ "$exit_code" = "0" ]; then
            echo "  Migrations complete." >&2
            break
        else
            echo "ERROR: Migrator exited with code $exit_code" >&2
            $COMPOSE logs test-migrator 2>&1 | tail -20 >&2
            exit 1
        fi
    fi
    sleep 2
done

# Wait for API to be ready
echo "==> Waiting for API..." >&2
for i in $(seq 1 30); do
    if curl -sf http://localhost:18000/api/v1/users/me/ -H "X-Api-Key: dummy" -o /dev/null 2>/dev/null; then
        echo "  API is responding (auth errors expected, that's fine)." >&2
        break
    fi
    # Also accept 401/403 as "API is up"
    code=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:18000/api/v1/users/me/ -H "X-Api-Key: dummy" 2>/dev/null || echo "000")
    if [ "$code" != "000" ]; then
        echo "  API is responding (HTTP $code)." >&2
        break
    fi
    sleep 2
done

# Seed test data via Django shell
echo "==> Seeding test user, workspace, and API token..." >&2
API_KEY=$($COMPOSE exec -T test-api python manage.py shell --settings=plane.settings.local -c "
import uuid
from plane.db.models import User, Workspace, WorkspaceMember, APIToken

# Create or get test user
user, _ = User.objects.get_or_create(
    email='test@test.com',
    defaults={
        'username': 'test@test.com',
        'first_name': 'Test',
        'last_name': 'User',
        'is_active': True,
        'is_password_autoset': False,
    }
)
user.set_password('TestPass123!')
user.save()

# Create or get workspace
ws, _ = Workspace.objects.get_or_create(
    slug='test-workspace',
    defaults={
        'name': 'Test Workspace',
        'owner': user,
    }
)

# Ensure membership (role=20 = Admin)
WorkspaceMember.objects.get_or_create(
    workspace=ws,
    member=user,
    defaults={'role': 20},
)

# Create service API token
token, created = APIToken.objects.get_or_create(
    user=user,
    workspace=ws,
    label='test-service-token',
    defaults={
        'is_service': True,
    }
)

print(str(token.token))
" 2>/dev/null)

if [ -z "$API_KEY" ]; then
    echo "ERROR: Failed to seed test data. Check container logs:" >&2
    $COMPOSE logs test-api 2>&1 | tail -30 >&2
    exit 1
fi

# Trim whitespace
API_KEY=$(echo "$API_KEY" | tr -d '[:space:]')

# Seed email references for email tests
echo "==> Seeding email references..." >&2
$COMPOSE exec -T test-api python manage.py shell --settings=plane.settings.local -c "
from plane.db.models import Workspace, EmailReference
from django.utils import timezone
from datetime import timedelta

ws = Workspace.objects.get(slug='test-workspace')
now = timezone.now()

emails = [
    {
        'message_id': 'test-msg-001@test.com',
        'subject': 'Test Email for unlink verification',
        'from_address': 'sender@test.com',
        'to_addresses': 'test@test.com',
        'folder': 'INBOX',
        'body_preview': 'Testing email link/unlink operations',
        'body_plain': 'Full body text for test email 1',
        'date': now,
    },
    {
        'message_id': 'test-msg-002@test.com',
        'subject': 'Intervan EDI setup request',
        'from_address': 'partner@example.com',
        'to_addresses': 'support@intervan.com',
        'folder': 'INBOX',
        'body_preview': 'We need to set up EDI with your team',
        'body_plain': 'Full body for EDI setup email',
        'date': now - timedelta(days=1),
    },
    {
        'message_id': 'test-msg-003@test.com',
        'subject': 'RE: Map code 4010 issue',
        'from_address': 'ops@intervan.com',
        'to_addresses': 'partner@example.com',
        'folder': 'Sent',
        'body_preview': 'The map code has been updated',
        'body_plain': 'Full body for map code email',
        'date': now - timedelta(days=2),
    },
    {
        'message_id': 'test-msg-004@test.com',
        'subject': 'Transaction 850 failure report',
        'from_address': 'alerts@messageway.com',
        'to_addresses': 'support@intervan.com',
        'folder': 'INBOX',
        'body_preview': 'Transaction failed for partner XYZ',
        'body_plain': 'Full body for failure report',
        'date': now - timedelta(hours=6),
        'triaged_at': now,
    },
    {
        'message_id': 'test-msg-005@test.com',
        'subject': 'Weekly Messageway Report',
        'from_address': 'reports@messageway.com',
        'to_addresses': 'support@intervan.com',
        'folder': 'INBOX',
        'body_preview': 'Weekly summary of transactions',
        'body_plain': 'Full body for weekly report',
        'date': now - timedelta(days=3),
        'triaged_at': now,
    },
]

created = 0
for data in emails:
    _, was_created = EmailReference.objects.get_or_create(
        workspace=ws,
        message_id=data['message_id'],
        defaults=data,
    )
    if was_created:
        created += 1
print(f'  {created} new, {EmailReference.objects.filter(workspace=ws).count()} total')
" 2>/dev/null >&2

echo "==> Test stack ready!" >&2
echo "  URL:       http://localhost:18000" >&2
echo "  Workspace: test-workspace" >&2
echo "  API Key:   ${API_KEY:0:8}..." >&2
echo "" >&2

# Output export commands for eval
echo "export PLANE_BASE_URL=http://localhost:18000"
echo "export PLANE_WORKSPACE_SLUG=test-workspace"
echo "export PLANE_API_KEY=$API_KEY"
