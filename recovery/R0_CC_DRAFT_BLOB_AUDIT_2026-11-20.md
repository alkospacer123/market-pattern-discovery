# R0 — CC historical Draft, per-file Git SHA-1 audit (20.11.2026)

Branch heads pinned: #544=7f7bc38e, #559=650e6f5a, #561=b2c2aa31. Reference MAIN commit: e6b8480b493365e0a4ff2bb56041891fde0a6f22.

Source SHA is Git blob SHA-1, **not** SHA256 or independent archived copy. Same path comparison checks current MAIN, not global content uniqueness.

| PR | Path | Draft blob SHA-1 | Size (bytes) | Compared to MAIN | MAIN blob SHA-1 |
|---|---|---|---:|---|---|
| #544 | `ControlCenter/deployment/manifest.json` | `57580b8e6490e92acb1f30c747280c754b42d3bb` | 13889 | different | `7cd99f68f930f64ef74f17d50f6510fcd7f96691` |
| #544 | `ControlCenter/tests/test_cc03_b2_replace_native_fixture.py` | `87a9de1e1b4b1e2045b099109efe6420a3151ce8` | 2597 | absent | — |
| #559 | `ControlCenter/README.md` | `7ae51dd25979f601ca8a03a5c165bf06d0acc8ae` | 12964 | different | `707080ee4daf1b2cf3a754c078a67e78f6612aae` |
| #559 | `ControlCenter/ci/file_open_trace.py` | `ac2fde26ae5c60ad878dca8034e9a432b6e1cf52` | 6892 | different | `b50844f1ff61b90beb58a311a6d476aedba3fa2e` |
| #559 | `ControlCenter/ci/protected-main-tree.json` | `45dee9359bf3df459570bce0a413e95b8e3ae929` | 2263 | different | `ff07b592289d975fe644a79f9d1d32f32a003d7a` |
| #559 | `ControlCenter/ci/source_feasibility_audit.py` | `5fa038220d84a351035fe6c2cbc2f4bc65153db4` | 2491 | absent | — |
| #559 | `ControlCenter/ci/windows_acceptance.py` | `417d98a2c13793f673ed21898d67818714beac44` | 15591 | different | `c86afa9cea21ae67131bb9c696d79cfdfd48f3a9` |
| #559 | `ControlCenter/deployment/manifest.json` | `fd482df780eb8dee3688180bd7152df469b96457` | 18158 | different | `7cd99f68f930f64ef74f17d50f6510fcd7f96691` |
| #559 | `ControlCenter/docs/CC03_H1_SOURCE_EVIDENCE.json` | `69e393a941ccd9478b53f6d098c66c88521307ae` | 8164 | absent | — |
| #559 | `ControlCenter/docs/CC03_H1_SOURCE_FEASIBILITY.md` | `1bdd8386ad45bba32a47c9f97a40fa05a66bbcad` | 17624 | absent | — |
| #559 | `ControlCenter/docs/CC03_H1_SOURCE_OPERATOR_CHECKPOINT.md` | `003f16092792e051963df82d204a0e29c683de91` | 4046 | absent | — |
| #559 | `ControlCenter/tests/test_source_feasibility.py` | `30ce5b4083d0703221acf614260db663f28ef748` | 5346 | absent | — |
| #559 | `ControlCenter/tests/test_windows_transport.py` | `49f95a24e46793f24e1c691447e3bd55858cfa7a` | 12176 | different | `e86e1eee1b6409a16efb9f379d7a4c60f482d40a` |
| #561 | `ControlCenter/app.py` | `6eeab02a31872b761e0a204363937e6739e5a727` | 7707 | different | `f82154c78290a4ff0a4052098ca91ac69d260eda` |
| #561 | `ControlCenter/broker_readonly/__init__.py` | `ed04f07cbdefb8deec11fb7c70bba851a058d48d` | 169 | absent | — |
| #561 | `ControlCenter/broker_readonly/contract.py` | `f34f3e58c3b4bcdc836c3dc16c403b12388706ba` | 7224 | absent | — |
| #561 | `ControlCenter/broker_readonly/finam-one-shot-operator.ps1` | `4b5ade4e5b718a748b153406f7db64029fef73a0` | 7363 | absent | — |
| #561 | `ControlCenter/broker_readonly/publish-from-one-shot.ps1` | `829f7a4270011cfda2c2dc3993b73a1d2697f2b2` | 8047 | absent | — |
| #561 | `ControlCenter/broker_readonly/publish-local-h1-check.ps1` | `512004cdeb1f0ba9b5a70b480d3ca633312a59d8` | 3354 | absent | — |
| #561 | `ControlCenter/cc/providers/h1_broker_snapshot.py` | `478c14d4638a2d3dcecc2170253596ed6caedda4` | 6997 | absent | — |
| #561 | `ControlCenter/cc/providers/h1_operator_report.py` | `aa860f6f271f651ff8abbde28d7a07ffcb704bde` | 6348 | absent | — |
| #561 | `ControlCenter/cc/ui.py` | `0080397e974bbc8d05247a17a6374452af2c2b3c` | 24868 | different | `03c4dde76d2beb6976ae1a1b7c9da8b392b1a5da` |
| #561 | `ControlCenter/ci/streamlit_click.py` | `565582fa37aed54afe55461e4e462b3ffc578cf2` | 9357 | different | `1680b24e0c21d0300536b0361bbfcac0fc9f0c24` |
| #561 | `ControlCenter/ci/windows_acceptance.py` | `ef7d34b8dfae40e904a912d9b97dfde62932f27d` | 15066 | different | `c86afa9cea21ae67131bb9c696d79cfdfd48f3a9` |
| #561 | `ControlCenter/deployment/broker-readonly-policy.example.json` | `6359689ec3869114fcd1570b5c654819da7f89f4` | 418 | absent | — |
| #561 | `ControlCenter/deployment/manifest.json` | `7b8ae287cb88f5e9d43b6da861212ee06047a742` | 19526 | different | `7cd99f68f930f64ef74f17d50f6510fcd7f96691` |
| #561 | `ControlCenter/deployment/manifest.py` | `c75fd2f2e3e722ba6a377c6f9e0bf34027820116` | 2899 | different | `f71e85d79ac9ce70f6d3572c7ec6f002570232ec` |
| #561 | `ControlCenter/docs/CC03_BROKER_SNAPSHOT_RELEASE.md` | `3c5191b607c5421d06075e19e18366bf3677a6a8` | 5368 | absent | — |
| #561 | `ControlCenter/docs/CC03_FINAM_READONLY_ONE_SHOT_DESIGN.md` | `cd492583193d3724c252053da18c1f01d2ceac5d` | 3616 | absent | — |
| #561 | `ControlCenter/tests/test_boundary.py` | `9400543397eaf15932cabc777289dc1b8c0b4831` | 5585 | different | `3843bc9dfa4acef7001e51ee09265f573bd17ba2` |
| #561 | `ControlCenter/tests/test_broker_readonly_contract.py` | `0db1bde3cd994f0f37e35f85a9de4126ae2e304f` | 4565 | absent | — |
| #561 | `ControlCenter/tests/test_broker_readonly_operator_ps.py` | `d39f2c1536a4df1c66e30b9c5841bb470bd39e56` | 2322 | absent | — |
| #561 | `ControlCenter/tests/test_broker_snapshot.py` | `2a76e0ed5ab36faff5bea667bb4edb2acce05efa` | 8123 | absent | — |
| #561 | `ControlCenter/tests/test_cc03_source.py` | `6bfcec439bc72ae8df75bae30bd9f3ca394deb00` | 12829 | different | `51f7c5f09c4920bbbe35c8f1b174bfbbb05763b5` |
| #561 | `ControlCenter/tests/test_h1_operator_report.py` | `afea0c35d9f30f421309e79e9403c186f5a1af14` | 3941 | absent | — |
| #561 | `ControlCenter/tests/test_h1_ui.py` | `8676319697f3534da44edec2db0e38cf0b22d997` | 4720 | different | `5f0fd4a9ff2f5c1b38f04f63e61a9a63b3bceb84` |
| #561 | `ControlCenter/tests/test_manual_os.py` | `6efb2e0df788d52d23f10f548cb830c6d1dbc4a5` | 17144 | different | `20bea1e7a5b25b45e6a765f7a9a135bb259822b4` |
| #561 | `ControlCenter/tests/test_os_observer.py` | `0ae54621dd669a931004f665a0333a78e1d7f763` | 10176 | different | `ff8e7846cdae01d365fdf742be2424f54860e10f` |
| #561 | `ControlCenter/tests/test_os_windows_native.py` | `4d69548a5fb733ea91ff0378e84b0f44ce4a3692` | 11864 | different | `c76dd493335ea8a8c03bbb5f53bf377a15a40bd5` |
| #561 | `ControlCenter/tests/test_ui.py` | `25721761219076bafa1e07d0654219d6d0e62745` | 3746 | different | `b75271952558ca437f6e94f5f28d34318714cf96` |


**Interpretation:** `absent` means no file at the same path in accepted MAIN; `different` means the path exists but bytes differ; `same` means identical blob content. No interpretation of deployment or scientific validity implied. Archive/close remains pending independent history capture and operator approval.
