# GitHub Actions Workflows

This project uses GitHub Actions for automated testing and daily simulations.

## Workflows

### 1. Tests (`test.yml`)

**Trigger**: On every push and pull request to `main` or `develop` branches

**What it does**:
- Runs full test suite across Python 3.10, 3.11, and 3.12
- Generates code coverage reports
- Runs linting checks (flake8, black, isort)
- Uploads test artifacts

**Status Badge**:
```markdown
![Tests](https://github.com/YOUR_USERNAME/yield_guard_bot/workflows/Tests/badge.svg)
```

**Steps**:
1. Checkout code
2. Set up Python (matrix: 3.10, 3.11, 3.12)
3. Cache pip dependencies
4. Install dependencies
5. Run pytest with coverage
6. Upload coverage report (artifacts)
7. Run linting checks

**Expected Duration**: ~2-3 minutes

### 2. Daily Simulation (`daily_simulation.yml`)

**Trigger**:
- Scheduled: Every day at 2:00 AM UTC (9:00 PM EST)
- Manual: Via workflow dispatch

**What it does**:
- Runs conservative strategy simulation with live market data
- Saves results to persistent database (via cache)
- Generates summary report
- Uploads artifacts for 90-day retention
- Alerts on significant losses (>2%)

**Status Badge**:
```markdown
![Daily Simulation](https://github.com/YOUR_USERNAME/yield_guard_bot/workflows/Daily%20Simulation/badge.svg)
```

**Steps**:
1. Checkout code
2. Set up Python 3.11
3. Cache dependencies
4. Restore previous database from cache
5. Run simulation (`scripts/daily_simulation.py`)
6. Save updated database to cache
7. Generate summary report
8. Upload artifacts
9. Check for significant losses

**Expected Duration**: ~3-5 minutes

**Data Persistence**:
- Database is stored using GitHub Actions cache
- Cache key: `simulation-db-{run_number}`
- Artifacts retained for 90 days

## Manual Workflow Triggers

You can manually trigger the daily simulation workflow:

1. Go to **Actions** tab in GitHub
2. Select **Daily Simulation** workflow
3. Click **Run workflow**
4. Choose branch (default: main)
5. Click **Run workflow**

## Viewing Results

### Test Results

1. Go to **Actions** tab
2. Click on any **Tests** workflow run
3. View test summary in the workflow summary
4. Download coverage report from artifacts

### Simulation Results

1. Go to **Actions** tab
2. Click on any **Daily Simulation** workflow run
3. View summary in the workflow summary
4. Download `simulation-results-{run_number}` artifact for full data

**Artifact Contents**:
- `simulations.db` - SQLite database with all historical runs
- `simulation_summary.txt` - Text summary of recent runs

## Setup Requirements

### Secrets

No secrets are currently required for basic operation. Optional secrets for future enhancements:

- `SLACK_WEBHOOK` - For Slack notifications
- `EMAIL_ADDRESS` - For email alerts
- `DATABASE_URL` - For external database (PostgreSQL, etc.)

### Repository Settings

Ensure GitHub Actions is enabled:
1. Go to **Settings** > **Actions** > **General**
2. Set **Actions permissions** to "Allow all actions"
3. Enable **Read and write permissions** for workflows

## Notifications

### Current Behavior

- ✅ Workflow runs successfully → No notification
- ⚠️ Small loss (<2%) → Warning in logs, workflow succeeds
- 🚨 Significant loss (>2%) → Workflow fails, triggers notify job

### Adding Notifications

To add Slack notifications on failure:

1. Add Slack webhook URL as secret: `SLACK_WEBHOOK`
2. Update `daily_simulation.yml` notify job:

```yaml
- name: Send Slack notification
  uses: slackapi/slack-github-action@v1
  with:
    webhook: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "⚠️ Yield Guard Bot: Daily simulation failed",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*Daily Simulation Alert*\nSimulation failed or detected significant losses.\n<${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}|View Workflow>"
            }
          }
        ]
      }
```

## Monitoring

### Key Metrics to Monitor

1. **Test Success Rate**: Should be 100%
2. **Simulation Success Rate**: Track over time
3. **Average Return**: Monitor daily returns
4. **Max Drawdown**: Ensure stays under 10%
5. **Protocol Availability**: Check for "No data" errors

### Recommended Alerts

- Test failures on main branch
- Simulation failures (API issues, errors)
- Significant losses (>2% daily)
- Unusual patterns (3+ days of losses)

## Cost Considerations

GitHub Actions is free for public repositories with generous limits:

- **2,000 minutes/month** for private repos (free tier)
- **Unlimited** for public repos

**Estimated Usage**:
- Tests: ~3 min/run × ~10 runs/day = ~30 min/day = ~900 min/month
- Daily simulation: ~5 min/day = ~150 min/month
- **Total**: ~1,050 min/month (within free tier for public repos)

## Troubleshooting

### Test Workflow Fails

1. Check Python version compatibility
2. Verify all dependencies in requirements.txt
3. Review test logs in workflow run
4. Run tests locally: `pytest tests/ -v`

### Daily Simulation Fails

**"No market data available"**:
- Check DefiLlama API status
- Verify protocol names are correct
- Check network connectivity

**Database errors**:
- Check cache restore/save steps
- Verify data directory exists
- Check disk space (unlikely in GitHub Actions)

**Import errors**:
- Verify all dependencies installed
- Check requirements.txt is up to date

### Cache Issues

If database cache gets corrupted:

1. Go to **Actions** > **Caches**
2. Delete `simulation-db-*` caches
3. Re-run workflow (will start fresh)

## Development Workflow

### Before Pushing

1. Run tests locally:
   ```bash
   pytest tests/ -v
   ```

2. Check linting:
   ```bash
   flake8 src/
   black --check src/ tests/
   isort --check src/ tests/
   ```

3. Fix issues:
   ```bash
   black src/ tests/
   isort src/ tests/
   ```

### Branch Protection (Recommended)

Set up branch protection for `main`:

1. Go to **Settings** > **Branches**
2. Add rule for `main`
3. Enable:
   - ✅ Require pull request before merging
   - ✅ Require status checks to pass (Tests workflow)
   - ✅ Require branches to be up to date

## Future Enhancements

Potential workflow improvements:

- [ ] Deploy to production after tests pass
- [ ] Create release on version tag
- [ ] Build and publish Docker image
- [ ] Run security scans (Dependabot, CodeQL)
- [ ] Performance benchmarks
- [ ] Integration tests with test network
- [ ] Multi-strategy comparison
- [ ] Weekly/monthly reports
- [ ] Automatic issue creation on failures

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Actions Marketplace](https://github.com/marketplace?type=actions)
