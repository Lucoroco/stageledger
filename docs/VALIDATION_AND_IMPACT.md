# Evidence, validation and impact

This document separates verified engineering facts from future adoption targets.

## What can be verified today

- The project source code is publicly accessible in this repository.
- The CLI accepts local CSV/JSON inventory and event JSON.
- The browser dashboard at `web/index.html` supports local event authoring, imports and downloadable reports without external scripts or accounts.
- A Node.js test suite includes tests comparing browser calculations with Python on the same fictional example; see the `Browser and parity tests` Actions workflow.
- Unit tests are provided in `tests/` and can be run with `python -m unittest discover -s tests -v`.
- GitHub Actions is configured to test supported Python versions on push and pull requests; verify actual runs in the Actions tab.
- Documentation, sample inputs, licence and contributing instructions are available.

## Not yet established

- Active independent users or organisations
- Package registry downloads
- External contributors or merged external PRs
- Dependents / community adoption
- OpenSSF criticality score

**Do not report targets as achieved metrics.** The author should collect reproducible evidence (dates, public links, anonymised user testimonials with permission) before citing impact in an application.

## Field validation protocol

1. Ask a real event organiser to try the documented quick start without live or private data.
2. With permission, record the organisation type and general use case.
3. Collect concrete feedback: what worked, what was confusing, where the calculation differed from manual planning.
4. Open an issue for reproducible bugs; fix them and link the merged PR.
5. Record adoption evidence only after an independent user confirms use.

## Evidence table

| Metric | Current evidence | Verification method |
| --- | --- | --- |
| Public source | GitHub repository | Open this repository |
| Runnable Python tests | `tests/` | Run command above / inspect CI |
| Browser calculation tests and Python parity | `web/tests/` | Run `node --test web/tests/*.test.cjs` / inspect CI |
| Offline graphical dashboard | `web/index.html` | Download the repository and open locally |
| External users | Not verified | Independent user confirmation |
| Monthly package downloads | Not published / not verified | Registry dashboard |
| External merged PR contributors | Not verified | GitHub merged-PR history |
| Dependent projects | Not verified | GitHub dependents / registry |

## Use of AI-assisted development

Development and documentation have been assisted by AI. Review, testing and ongoing responsibility remain with the repository maintainer. AI-generated commits should not be represented as independent human community contributions.
