# GitHub Actions Setup

This directory contains GitHub Actions workflows for automated testing and daily simulations.

## Quick Start

1. **Push to GitHub**: Workflows are automatically enabled when you push this repository to GitHub

2. **View Workflows**: Go to the **Actions** tab in your GitHub repository

3. **Manual Trigger**: You can manually run the daily simulation workflow via the Actions tab

## Workflows

### 🧪 Tests (`workflows/test.yml`)

Runs automatically on every push and pull request.

- Tests across Python 3.10, 3.11, 3.12
- Generates coverage reports
- Runs linting checks
- Status: ![Tests](https://github.com/YOUR_USERNAME/yield_guard_bot/workflows/Tests/badge.svg)

### 📊 Daily Simulation (`workflows/daily_simulation.yml`)

Runs automatically every day at 2:00 AM UTC.

- Executes conservative strategy simulation
- Saves results to database
- Uploads artifacts for 90 days
- Alerts on significant losses
- Status: ![Daily Simulation](https://github.com/YOUR_USERNAME/yield_guard_bot/workflows/Daily%20Simulation/badge.svg)

## First-Time Setup

### 1. Enable GitHub Actions

GitHub Actions should be enabled by default. If not:

1. Go to **Settings** > **Actions** > **General**
2. Select "Allow all actions"
3. Enable "Read and write permissions"

### 2. Verify Workflows

After pushing to GitHub:

1. Go to **Actions** tab
2. You should see "Tests" workflow run automatically
3. Daily Simulation will run on schedule or can be triggered manually

### 3. Test Manually (Optional)

Trigger the daily simulation manually to verify setup:

1. Go to **Actions** tab
2. Select **Daily Simulation** workflow
3. Click **Run workflow** button
4. Select branch (main)
5. Click **Run workflow**

## Monitoring Results

### Test Results

View test results in the Actions tab:
- Click on any "Tests" workflow run
- See test summary in the workflow summary
- Download coverage report from artifacts

### Simulation Results

View simulation results:
- Click on any "Daily Simulation" workflow run
- See summary with returns and metrics
- Download database and full results from artifacts

## Data Persistence

The daily simulation uses GitHub Actions cache for database persistence:

- **Cache Key**: `simulation-db-{run_number}`
- **Database File**: `data/simulations.db`
- **Retention**: Cache expires after 7 days of no access
- **Artifacts**: Kept for 90 days as backup

**Note**: The database grows over time. Artifacts provide long-term backup if cache expires.

## Notifications (Optional)

To receive notifications on failures:

### Slack

1. Create a Slack webhook URL
2. Add as repository secret: `SLACK_WEBHOOK`
3. Update `daily_simulation.yml` notify job (see WORKFLOWS.md)

### Email

GitHub sends email notifications by default for workflow failures to the repository owner.

## Troubleshooting

### Workflow Not Running

**Scheduled workflow doesn't run**:
- Workflows may be disabled if repository inactive for 60 days
- Re-enable in Actions tab

**Tests fail on push**:
- Check Python version compatibility
- Verify dependencies in requirements.txt
- Run tests locally: `pytest tests/ -v`

### Database Issues

**Cache not restoring**:
- Check workflow logs for cache restore step
- Cache may have expired (7 days)
- Download artifact from previous run to restore

**Database growing too large**:
- GitHub cache limit: 10 GB per repository
- Consider external database (PostgreSQL, etc.)

## Cost & Limits

GitHub Actions free tier:

- **Public repositories**: Unlimited minutes
- **Private repositories**: 2,000 minutes/month

Estimated usage:
- Tests: ~900 min/month
- Daily simulation: ~150 min/month
- **Total**: ~1,050 min/month ✅ (within free tier)

## Security

### Secrets Management

Currently no secrets required. For future enhancements:

**To add secrets**:
1. Go to **Settings** > **Secrets and variables** > **Actions**
2. Click **New repository secret**
3. Add name and value
4. Reference in workflow: `${{ secrets.SECRET_NAME }}`

### Permissions

Workflows have read/write permissions to:
- Repository contents (code)
- Actions cache
- Artifacts

**Note**: Workflows cannot access other repositories or external resources without explicit configuration.

## Advanced Configuration

### Change Schedule

Edit `.github/workflows/daily_simulation.yml`:

```yaml
on:
  schedule:
    # Daily at 2 AM UTC
    - cron: '0 2 * * *'

    # Or every 12 hours
    - cron: '0 */12 * * *'

    # Or weekdays only at 9 AM
    - cron: '0 9 * * 1-5'
```

### Add More Strategies

Extend daily simulation to run multiple strategies:

```yaml
- name: Run conservative simulation
  run: python scripts/daily_simulation.py --capital 1000000 --days 1

- name: Run moderate simulation (future)
  run: python scripts/daily_simulation.py --strategy moderate --capital 1000000 --days 1
```

### Branch Protection

Recommended for production:

1. Go to **Settings** > **Branches**
2. Add rule for `main`
3. Require:
   - Pull request before merging
   - Status checks to pass (Tests)
   - Branches to be up to date

## Resources

- [WORKFLOWS.md](WORKFLOWS.md) - Detailed workflow documentation
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)

## Support

If you encounter issues:

1. Check workflow logs in Actions tab
2. Review [WORKFLOWS.md](WORKFLOWS.md) troubleshooting section
3. Test locally before pushing
4. Create issue with workflow run URL
