# GitHub Actions Scraping Guide

Complete guide to scrape medical content using GitHub Actions.

---

## Quick Start (5 minutes)

### Step 1: Merge the Branch

First, merge the `claude/review-codebase-EBJP2` branch to your main branch:

```bash
git checkout main
git merge claude/review-codebase-EBJP2
git push origin main
```

Or create a Pull Request on GitHub and merge it.

### Step 2: Run the Workflow

1. Go to your repository on GitHub: `https://github.com/YOUR_USERNAME/scrapy`

2. Click the **"Actions"** tab

3. In the left sidebar, click **"Scrape Medical Content"**

4. Click the **"Run workflow"** button (on the right side)

5. Configure options:
   - **Site to scrape**: Choose `all`, `mdcafe`, or `msdmanuals`
   - **Maximum pages**: Enter a number (default: 100)
   - **Use Playwright**: Keep checked for better results

6. Click **"Run workflow"** (green button)

### Step 3: Wait for Completion

- The workflow takes 5-30 minutes depending on settings
- Watch progress in the Actions tab
- Content auto-commits to your repo when done

### Step 4: View Results

After completion, scraped content is in:
```
medical_scraper/output/
├── md_cafe/
│   ├── html/      # Raw HTML files
│   ├── text/      # Plain text content
│   └── json/      # Metadata
└── msdmanuals/
    ├── html/
    ├── text/
    └── json/
```

---

## Detailed Instructions

### Accessing GitHub Actions

1. **Navigate to your repository**
   ```
   https://github.com/YOUR_USERNAME/scrapy
   ```

2. **Click the "Actions" tab**

   ![Actions Tab](https://docs.github.com/assets/cb-15465/mw-1440/images/help/repository/actions-tab-global-nav-update.webp)

3. **Find the workflow**

   In the left sidebar, you'll see "Scrape Medical Content"

### Running the Workflow

1. **Click "Run workflow"**

   You'll see a dropdown with options:

   | Option | Description | Recommended |
   |--------|-------------|-------------|
   | **Site** | Which site(s) to scrape | `all` for both sites |
   | **Max pages** | Limit pages per site | `50` for testing, `100`+ for full scrape |
   | **Use Playwright** | Enable JavaScript rendering | `true` (checked) |

2. **Start the workflow**

   Click the green "Run workflow" button

### Monitoring Progress

1. **Click on the running workflow**

   You'll see it appear in the list with a yellow dot (running)

2. **View live logs**

   Click on "scrape" job to see real-time output:
   ```
   Running spider: mdcafe_pw
   2024-01-20 10:30:15 [scrapy.core.engine] INFO: Spider opened
   2024-01-20 10:30:16 [scrapy.core.engine] DEBUG: Crawled (200) <GET https://md.cafe/>
   ...
   ```

3. **Wait for completion**

   - Green checkmark = success
   - Red X = failed (check logs for errors)

### Downloading Results

**Option A: From Repository**

After the workflow completes, content is committed to:
```
medical_scraper/output/
```

Pull the latest changes:
```bash
git pull origin main
```

**Option B: Download Artifact**

1. Go to the completed workflow run
2. Scroll to "Artifacts" section at the bottom
3. Click "scraped-content" to download ZIP
4. Artifacts are kept for 30 days

---

## Configuration Options

### Change Scraping Depth

Edit `medical_scraper/medical_scraper/settings.py`:
```python
DEPTH_LIMIT = 5  # Increase for more pages
```

### Change Request Delay

```python
DOWNLOAD_DELAY = 3  # Seconds between requests
```

### Schedule Automatic Scraping

Edit `.github/workflows/scrape-medical-content.yml`:

```yaml
on:
  workflow_dispatch:  # Keep manual trigger
  schedule:
    - cron: '0 0 * * 0'  # Every Sunday at midnight UTC
```

Common schedules:
| Schedule | Cron Expression |
|----------|-----------------|
| Daily at midnight | `0 0 * * *` |
| Weekly on Sunday | `0 0 * * 0` |
| Monthly on 1st | `0 0 1 * *` |

---

## Troubleshooting

### Workflow not visible

**Cause**: Branch not merged to main

**Fix**: Merge the branch first:
```bash
git checkout main
git merge claude/review-codebase-EBJP2
git push
```

### "Run workflow" button missing

**Cause**: Need write access to repository

**Fix**: Ensure you're the owner or have write permissions

### Scraping fails with 403 errors

**Cause**: Site blocking automated requests

**Fixes**:
1. Ensure "Use Playwright" is checked
2. Reduce max pages
3. The workflow continues on error - partial content still saves

### No content scraped

**Cause**: Site structure changed or blocking

**Check**:
1. View workflow logs for errors
2. Try running locally first
3. Update spider selectors if site changed

### Workflow times out

**Cause**: Too many pages requested

**Fix**: Reduce "Maximum pages" to 50 or less

---

## Output Format

### JSON Metadata
```json
{
  "url": "https://md.cafe/cardiology/heart-failure",
  "title": "Heart Failure - Diagnosis and Treatment",
  "source": "md_cafe",
  "category": "Cardiology",
  "subcategory": "Heart Conditions",
  "breadcrumbs": ["Cardiology", "Heart Conditions", "Heart Failure"],
  "last_updated": "2024-01-15",
  "scraped_at": "2024-01-20T10:30:00Z",
  "filename": "Heart-Failure-Diagnosis-and-Treatment_84664295"
}
```

### Text Format
```
Title: Heart Failure - Diagnosis and Treatment
================================================================================
Source URL: https://md.cafe/cardiology/heart-failure
Category: Cardiology
Path: Cardiology > Heart Conditions > Heart Failure

--------------------------------------------------------------------------------

Heart failure is a chronic condition where the heart doesn't pump...
```

### HTML Format
Original HTML content with metadata in `<head>`.

---

## Repository Permissions

The workflow needs permission to push commits. This is configured automatically, but if you see permission errors:

1. Go to **Settings** → **Actions** → **General**
2. Under "Workflow permissions", select **"Read and write permissions"**
3. Save

---

## Cost

GitHub Actions is **free** for public repositories and includes:
- 2,000 minutes/month for private repos (free tier)
- Unlimited for public repos

The scraping workflow typically uses 5-20 minutes per run.

---

## Support

If you encounter issues:
1. Check the workflow logs for specific errors
2. Verify the branch is merged
3. Try with fewer pages first
4. Open an issue in the repository
