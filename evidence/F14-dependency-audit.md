# F11 deps sweep — 2026-10-10
## pip-audit (backend; no requirements.txt in repo, versions = installed in dev env: fastapi==0.115.0 pydantic==2.13.3 pymongo==4.15.3 python-dotenv==1.0.1 uvicorn==0.32.0 )
WARNING:pip_audit._cli:--no-deps is supported, but users are encouraged to fully hash their pinned dependencies
WARNING:pip_audit._cli:Consider using a tool like `pip-compile`: https://pip-tools.readthedocs.io/en/latest/#using-hashes
Found 6 known vulnerabilities in 2 packages
Name          Version ID              Fix Versions
------------- ------- --------------- ------------
pymongo       4.15.3  CVE-2026-88029  4.18.1
pymongo       4.15.3  CVE-2026-96747  4.18.2
pymongo       4.15.3  CVE-2026-96749  4.18.2
pymongo       4.15.3  CVE-2026-96748  4.18.2
python-dotenv 1.0.1   PYSEC-2026-2270 1.2.2
python-dotenv 1.0.1   PYSEC-2026-2270 1.2.2

## npm audit (ABetterTerp frontend)
# npm audit report

@babel/core  <=7.29.0
@babel/core: Arbitrary File Read via sourceMappingURL Comment - https://github.com/advisories/GHSA-4x5r-pxfx-6jf8
fix available via `npm audit fix`
node_modules/@babel/core

@humanfs/node  <0.16.8
Severity: moderate
humanfs: Recursive copy follows symlinked files and copies data from outside the source tree - https://github.com/advisories/GHSA-p498-v437-472g
fix available via `npm audit fix`
node_modules/@humanfs/node

ajv  <6.14.0
Severity: moderate
ajv has ReDoS when using `$data` option - https://github.com/advisories/GHSA-2g4f-4pwh-qvx6
fix available via `npm audit fix`
node_modules/ajv

baseline-browser-mapping  >=2.0.0 <2.11.0
Severity: moderate
baseline-browser-mapping process termination on invalid input causes denial of service - https://github.com/advisories/GHSA-w5vr-8v7q-w6rv
fix available via `npm audit fix`
node_modules/baseline-browser-mapping

brace-expansion  <=1.1.20 || 2.0.0 - 2.1.6
Severity: high
brace-expansion: Zero-step sequence causes process hang and memory exhaustion - https://github.com/advisories/GHSA-f886-m6hf-6m8v
brace-expansion: Zero-step sequence causes process hang and memory exhaustion - https://github.com/advisories/GHSA-f886-m6hf-6m8v
brace-expansion: DoS via exponential-time expansion of consecutive non-expanding {} groups - https://github.com/advisories/GHSA-3jxr-9vmj-r5cp
brace-expansion: DoS via exponential-time expansion of consecutive non-expanding {} groups - https://github.com/advisories/GHSA-3jxr-9vmj-r5cp
brace-expansion: DoS via unbounded expansion length causing an out-of-memory process crash - https://github.com/advisories/GHSA-mh99-v99m-4gvg
brace-expansion: DoS via unbounded expansion length causing an out-of-memory process crash - https://github.com/advisories/GHSA-mh99-v99m-4gvg
brace-expansion: DoS via unbounded intermediate arrays, bypassing the CVE-2026-14257 mitigation - https://github.com/advisories/GHSA-rgw5-rvv9-x895
brace-expansion: DoS via unbounded intermediate arrays, bypassing the CVE-2026-14257 mitigation - https://github.com/advisories/GHSA-rgw5-rvv9-x895
brace-expansion: Quadratic-time expansion of the `{a},b}` rewrite causes CPU denial of service - https://github.com/advisories/GHSA-q2hr-2g5m-vwhr
brace-expansion: Quadratic-time expansion of the `{a},b}` rewrite causes CPU denial of service - https://github.com/advisories/GHSA-q2hr-2g5m-vwhr
brace-expansion: DoS via uncontrolled recursion on nested brace groups causing stack exhaustion - https://github.com/advisories/GHSA-qhr7-859c-m2p7
brace-expansion: DoS via uncontrolled recursion on nested brace groups causing stack exhaustion - https://github.com/advisories/GHSA-qhr7-859c-m2p7
brace-expansion: DoS via uncontrolled recursion in parseCommaParts causing stack exhaustion - https://github.com/advisories/GHSA-6j4f-fj2g-mc7p
brace-expansion: DoS via uncontrolled recursion in parseCommaParts causing stack exhaustion - https://github.com/advisories/GHSA-6j4f-fj2g-mc7p
fix available via `npm audit fix`
node_modules/@typescript-eslint/typescript-estree/node_modules/brace-expansion
node_modules/brace-expansion

braces  *
Severity: high
braces vulnerable to stack-exhaustion denial of service through deeply nested patterns - https://github.com/advisories/GHSA-vfj7-8cjw-p6xm
fix available via `npm audit fix`
node_modules/braces
  micromatch  >=0.2.0
  Depends on vulnerable versions of braces
  node_modules/micromatch
    fast-glob  *
    Depends on vulnerable versions of micromatch
    node_modules/fast-glob
      @typescript-eslint/typescript-estree  8.2.1-alpha.0 - 8.47.1-alpha.9
      Depends on vulnerable versions of fast-glob
      node_modules/@typescript-eslint/typescript-estree
        @typescript-eslint/parser  8.2.1-alpha.0 - 8.47.1-alpha.9
        Depends on vulnerable versions of @typescript-eslint/typescript-estree
        node_modules/@typescript-eslint/parser
        @typescript-eslint/type-utils  8.2.1-alpha.0 - 8.47.1-alpha.9
        Depends on vulnerable versions of @typescript-eslint/typescript-estree
        Depends on vulnerable versions of @typescript-eslint/utils
        node_modules/@typescript-eslint/type-utils
        @typescript-eslint/utils  8.2.1-alpha.0 - 8.47.1-alpha.9
        Depends on vulnerable versions of @typescript-eslint/typescript-estree
        node_modules/@typescript-eslint/utils
          @typescript-eslint/eslint-plugin  8.2.1-alpha.0 - 8.47.1-alpha.9
          Depends on vulnerable versions of @typescript-eslint/type-utils
          Depends on vulnerable versions of @typescript-eslint/utils
          node_modules/@typescript-eslint/eslint-plugin
          typescript-eslint  8.2.1-alpha.0 - 8.47.1-alpha.9
          Depends on vulnerable versions of @typescript-eslint/eslint-plugin
          Depends on vulnerable versions of @typescript-eslint/parser
          Depends on vulnerable versions of @typescript-eslint/typescript-estree
          Depends on vulnerable versions of @typescript-eslint/utils
          node_modules/typescript-eslint

browserslist  <=4.28.6
Severity: high
Browserslist: Unbounded memory growth (no cache eviction) via distinct query results, leading to eventual OOM - https://github.com/advisories/GHSA-c83g-rgw3-j3cx
Browserslist: Uncaught crash / prototype write via untrusted browserslist-stats.json custom stats (normalizeStats) - https://github.com/advisories/GHSA-73wf-gq98-2v4g
fix available via `npm audit fix`
node_modules/browserslist

flatted  <=3.4.1
Severity: high
flatted vulnerable to unbounded recursion DoS in parse() revive phase - https://github.com/advisories/GHSA-25h7-pfq9-p65f
Prototype Pollution via parse() in NodeJS flatted - https://github.com/advisories/GHSA-rf6f-7fwh-wjgh
fix available via `npm audit fix`
node_modules/flatted

js-yaml  4.0.0 - 4.3.1
Severity: high
JS-YAML: Quadratic-complexity DoS in merge key handling via repeated aliases - https://github.com/advisories/GHSA-h67p-54hq-rp68
js-yaml: YAML merge-key chains can force quadratic CPU consumption - https://github.com/advisories/GHSA-52cp-r559-cp3m
JS-YAML: Quadratic CPU consumption in !!omap resolution (3.x and 4.x) — CVE-2026-59870 fix not backported - https://github.com/advisories/GHSA-5p4m-2wfm-xmqj
js-yaml: maxTotalMergeKeys does not limit CPU use for empty merge sources - https://github.com/advisories/GHSA-2883-xcg3-v3hh
fix available via `npm audit fix`
node_modules/js-yaml

minimatch  <=3.1.3 || 9.0.0 - 9.0.6
Severity: high
minimatch has a ReDoS via repeated wildcards with non-matching literal in pattern - https://github.com/advisories/GHSA-3ppc-4f35-3m26
minimatch has a ReDoS via repeated wildcards with non-matching literal in pattern - https://github.com/advisories/GHSA-3ppc-4f35-3m26
minimatch has ReDoS: matchOne() combinatorial backtracking via multiple non-adjacent GLOBSTAR segments - https://github.com/advisories/GHSA-7r86-cg39-jmmj
minimatch has ReDoS: matchOne() combinatorial backtracking via multiple non-adjacent GLOBSTAR segments - https://github.com/advisories/GHSA-7r86-cg39-jmmj
minimatch ReDoS: nested *() extglobs generate catastrophically backtracking regular expressions - https://github.com/advisories/GHSA-23c5-xmqv-rm74
minimatch ReDoS: nested *() extglobs generate catastrophically backtracking regular expressions - https://github.com/advisories/GHSA-23c5-xmqv-rm74
fix available via `npm audit fix`
node_modules/@typescript-eslint/typescript-estree/node_modules/minimatch
node_modules/minimatch

nanoid  <=3.3.17
Severity: high
nanoid: non-secure generators can loop indefinitely with negative size - https://github.com/advisories/GHSA-28wg-ghj8-5hjv
nanoid: custom generators can loop indefinitely when size is zero - https://github.com/advisories/GHSA-2v37-7h3g-55p8
nanoid: Integer Overflow or Wraparound - https://github.com/advisories/GHSA-xwg4-73v4-xw9w
fix available via `npm audit fix`
node_modules/nanoid

picomatch  <=2.3.1 || 4.0.0 - 4.0.3
Severity: high
Picomatch: Method Injection in POSIX Character Classes causes incorrect Glob Matching - https://github.com/advisories/GHSA-3v7f-55p6-f55p
Picomatch: Method Injection in POSIX Character Classes causes incorrect Glob Matching - https://github.com/advisories/GHSA-3v7f-55p6-f55p
Picomatch has a ReDoS vulnerability via extglob quantifiers - https://github.com/advisories/GHSA-c2c7-rcm5-vvqj
Picomatch has a ReDoS vulnerability via extglob quantifiers - https://github.com/advisories/GHSA-c2c7-rcm5-vvqj
fix available via `npm audit fix`
node_modules/picomatch
node_modules/tinyglobby/node_modules/picomatch
node_modules/vite/node_modules/picomatch

postcss  <=8.5.22
Severity: high
PostCSS has XSS via Unescaped </style> in its CSS Stringify Output - https://github.com/advisories/GHSA-qx2v-qp2m-jg93
PostCSS: Arbitrary file read and information disclosure via attacker-controlled sourceMappingURL in CSS comments - https://github.com/advisories/GHSA-6g55-p6wh-862q
PostCSS: incomplete fix of GHSA-6g55-p6wh-862q — attacker-controlled sourceMappingURL reads arbitrary .map files when `from` is unset - https://github.com/advisories/GHSA-fxqj-rqcc-2cmp
PostCSS: Path Traversal in Previous Source Map Auto-Loading (sourceMappingURL) leads to Arbitrary .map File Disclosure - https://github.com/advisories/GHSA-r28c-9q8g-f849
fix available via `npm audit fix`
node_modules/postcss

react-router  6.0.0 - 7.17.0
Severity: high
React Router vulnerable to XSS via Open Redirects - https://github.com/advisories/GHSA-2w69-qvjg-hvjx
React Router's vendored turbo-stream v2 allows arbitrary constructor invocation via TYPE_ERROR deserialization leading to Unauth RCE - https://github.com/advisories/GHSA-49rj-9fvp-4h2h
React Router vulnerable to XSS in unstable RSC redirect handling via javascript: redirect targets - https://github.com/advisories/GHSA-8646-j5j9-6r62
React Router vulnerable to DoS via unbounded path expansion in __manifest endpoint - https://github.com/advisories/GHSA-8x6r-g9mw-2r78
React Router vulnerable to Denial of Service via reflected user input in single-fetch - https://github.com/advisories/GHSA-rxv8-25v2-qmq8
React Router has CSRF issue in Action/Server Action Request Processing - https://github.com/advisories/GHSA-h5cw-625j-3rxh
React Router: Open redirect via backslash in <Link> and useNavigate (CVE-2025-68470 bypass) - https://github.com/advisories/GHSA-wrjc-x8rr-h8h6
React Router: Arbitrary Constructor Injection via deserializeErrors() in React Router SSR Hydration - https://github.com/advisories/GHSA-337j-9hxr-rhxg
React Router: Unauthenticated Denial of Service via Inefficient Route Matching - https://github.com/advisories/GHSA-chx6-hx7r-mcp5
React Router's same-origin redirect with path starting // causes open redirect via protocol-relative URL reinterpretation - https://github.com/advisories/GHSA-2j2x-hqr9-3h42
React Router: Open redirect leading to XSS - https://github.com/advisories/GHSA-jjmj-jmhj-qwj2
React Router has stored XSS via unescaped Location header in prerendered redirect HTML - https://github.com/advisories/GHSA-f22v-gfqf-p8f3
React Router SSR XSS in ScrollRestoration - https://github.com/advisories/GHSA-8v8x-cx79-35w7
fix available via `npm audit fix`
node_modules/react-router
  react-router-dom  7.0.0-pre.0 - 7.11.0
  Depends on vulnerable versions of react-router
  node_modules/react-router-dom

rollup  4.0.0 - 4.58.0
Severity: high
Rollup 4 has Arbitrary File Write via Path Traversal - https://github.com/advisories/GHSA-mw96-cpmx-2vgc
fix available via `npm audit fix`
node_modules/rollup

source-map-js  1.0.0 - 1.2.1
Severity: high
source-map-js allows event-loop denial of service through indexed source-map section offsets - https://github.com/advisories/GHSA-68fv-2mgg-jv7q
fix available via `npm audit fix`
node_modules/source-map-js

vite  7.0.0 - 7.3.3
Severity: high
Vite Vulnerable to Path Traversal in Optimized Deps `.map` Handling - https://github.com/advisories/GHSA-4w7w-66w2-5vf9
Vite: `server.fs.deny` bypassed with queries - https://github.com/advisories/GHSA-v2wj-q39q-566r
Vite Vulnerable to Arbitrary File Read via Vite Dev Server WebSocket - https://github.com/advisories/GHSA-p9ff-h696-f583
launch-editor: NTLMv2 hash disclosure via UNC path handling on Windows - https://github.com/advisories/GHSA-v6wh-96g9-6wx3
vite: `server.fs.deny` bypass on Windows alternate paths - https://github.com/advisories/GHSA-fx2h-pf6j-xcff
fix available via `npm audit fix`
node_modules/vite

26 vulnerabilities (1 low, 3 moderate, 22 high)

To address all issues, run:
  npm audit fix
