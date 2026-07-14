# Releasing PortBoard

Only the repository owner publishes PortBoard. Releases originate from the
protected `main` branch and use the protected `v*` tag namespace.

## Release checklist

1. On `develop`, update the Python version in `pyproject.toml` and
   `src/portboard/__init__.py`.
2. Update the five npm `package.json` files under `packaging/npm/`. Python PEP
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

The workflow verifies the tag against the Python package version and verifies
that the tagged commit belongs to `main`. It builds wheels and source archives,
four native executables, five npm packages, and a checksum manifest. Prerelease
npm versions use the `next` dist-tag; stable versions use `latest`.

## First npm publication

npm trusted publishing can only be configured after each package exists. The
first npm release therefore needs a short-lived granular npm access token:

1. Create or sign in to the npm account that owns the `@leonpure` scope and
   enable two-factor authentication.
2. Create a granular token with permission to publish public packages in that
   scope, then add it temporarily as the `NPM_TOKEN` secret of the protected
   GitHub `npm` environment.
3. Run the normal tag release and approve the `npm` environment. The workflow
   publishes the four platform packages before `@leonpure/portboard`.
4. For each of the five packages on npmjs.com, configure a GitHub Actions
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
