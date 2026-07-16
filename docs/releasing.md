# Releasing PortBoard

Only the repository owner publishes PortBoard. Releases originate from the
protected `main` branch and use the protected `v*` tag namespace.

## Release checklist

1. On `develop`, update the Python version in `pyproject.toml` and
   `src/portboard/__init__.py`.
2. Update all seven npm `package.json` files under `packaging/npm/`. Python PEP
   440 prereleases map to npm SemVer: `0.1.0a2` becomes `0.1.0-alpha.2`, `b1`
   becomes `beta.1`, and `rc1` stays `rc.1`.
3. Move the release notes out of the changelog's `Unreleased` section and run:

   ```bash
   uv sync --locked
   uv run ruff check .
   uv run mypy
   uv run pytest
   uv build --no-sources
   npm test --prefix packaging/npm/portboard
   ```

4. Merge the owner-created `develop` to `main` release pull request with a
   merge commit after all required checks pass.
5. Create and push the matching annotated tag from the `main` merge commit:

   ```bash
   git tag -a v0.1.0a2 -m "PortBoard 0.1.0a2"
   git push origin v0.1.0a2
   ```

6. Approve the protected `pypi` and `npm` environments in GitHub Actions.
7. After the GitHub release succeeds, request a Homebrew formula update:

   ```bash
   gh workflow run update-portboard.yml \
     --repo LeonPure/homebrew-tap \
     -f tag=v0.1.0a2
   ```

   Open the pull request from the update branch link in the workflow summary,
   wait for all four platform checks, review it, and merge it. The tap's
   protected `main` branch does not accept direct pushes.

The workflow verifies the tag against the Python package version and verifies
that the tagged commit belongs to `main`. It builds wheels and source archives,
six native executables, four Homebrew archives, seven npm packages, and a
checksum manifest. Prerelease npm versions use the `next` dist-tag; stable
versions use `latest`.

## Homebrew tap

The `LeonPure/homebrew-tap` repository publishes the `portboard` formula. Its
manual update workflow accepts an existing PortBoard tag, verifies the release
archives against `SHA256SUMS`, and updates the formula on a release branch. The
repository owner opens the resulting pull request from the workflow summary.
The workflow uses only the tap repository's short-lived `GITHUB_TOKEN`; there
is no cross-repository secret.

Release archives must exist for `darwin-arm64`, `darwin-x64`, `linux-arm64`,
and `linux-x64`. The formula pull request must be reviewed and merged by the
repository owner before `brew update` can deliver it.

## Shell installer

The protected `main` branch publishes `install.sh` through GitHub's raw-content
endpoint. The installer selects the latest stable GitHub Release, falling back
to the newest prerelease only while no stable release exists. It downloads the
same platform archives used by Homebrew and refuses installation unless the
archive matches the release's `SHA256SUMS` entry. No separate installer
publication or credential is required.

## First npm publication or new platform package

npm trusted publishing can only be configured after each package exists. The
first npm release, and the first release of any newly added platform package,
therefore needs a short-lived granular npm access token:

1. Create or sign in to the npm account that owns the `@leonpure` scope and
   enable two-factor authentication.
2. Create a granular token with permission to publish public packages in that
   scope, then add it temporarily as the `NPM_TOKEN` secret of the protected
   GitHub `npm` environment.
3. Run the normal tag release and approve the `npm` environment. The workflow
   publishes the six platform packages before `@leonpure/portboard`.
4. For every newly created package on npmjs.com, configure a GitHub Actions
   trusted publisher with these exact values:

   - Organization or user: `LeonPure`
   - Repository: `portboard`
   - Workflow filename: `release.yml`
   - Environment: `npm`
   - Allowed action: `npm publish`

5. Delete the `NPM_TOKEN` GitHub secret and revoke the npm token. For each npm
   package, require two-factor authentication and disallow token publishing.

Later releases authenticate with short-lived GitHub OIDC credentials and
automatically include npm provenance. No long-lived publishing credential is
kept in the repository.
