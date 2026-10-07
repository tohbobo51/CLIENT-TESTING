#!/usr/bin/env python3
"""Apply the Vice Side single-server and CEF setup to the imported client."""

from pathlib import Path
import re
import sys


SERVER_HOST = "142.132.203.47"
SERVER_PORT = 10125
SERVER_NAME = "Vice Side Roleplay"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"Expected source section not found: {label}")
    return text.replace(old, new, 1)


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "client").resolve()
    manager_path = root / "app/src/main/java/com/xyron/game/launcher/util/ServerConfigManager.java"
    samp_path = root / "app/src/main/java/com/xyron/game/main/SAMP.java"
    gradle_path = root / "app/build.gradle"
    strings_path = root / "app/src/main/res/values/strings.xml"

    required = [
        manager_path,
        samp_path,
        gradle_path,
        root / "app/libs/sampmobilecef-1.0.0-release.aar",
        root / "jni/jni/vendor/cef/libSAMPMobileCef.a",
    ]
    missing = [str(path.relative_to(root)) for path in required if not path.exists()]
    if missing:
        raise SystemExit("Source archive is missing required files: " + ", ".join(missing))

    manager = manager_path.read_text(encoding="utf-8")
    manager = replace_once(
        manager,
        "    private static final int MAX_SAVED_SERVERS = 5;",
        (
            "    private static final int MAX_SAVED_SERVERS = 1;\n"
            f'    private static final String SINGLE_SERVER_HOST = "{SERVER_HOST}";\n'
            f"    private static final int SINGLE_SERVER_PORT = {SERVER_PORT};\n"
            f'    private static final String SINGLE_SERVER_NAME = "{SERVER_NAME}";'
        ),
        "single-server constants",
    )
    manager = replace_once(
        manager,
        "    public static List<ServerOption> getAvailableServers(Context context) {\n"
        "        return loadStoredServers(context);\n"
        "    }",
        "    public static List<ServerOption> getAvailableServers(Context context) {\n"
        "        ArrayList<ServerOption> servers = new ArrayList<>();\n"
        "        servers.add(new ServerOption(SINGLE_SERVER_NAME, SINGLE_SERVER_HOST, SINGLE_SERVER_PORT, true));\n"
        "        return servers;\n"
        "    }",
        "fixed server list",
    )
    manager = replace_once(
        manager,
        "        if (context == null || TextUtils.isEmpty(sanitize(host)) || !isValidPort(port)) {\n"
        "            return false;\n"
        "        }",
        "        if (context == null || TextUtils.isEmpty(sanitize(host)) || !isValidPort(port)) {\n"
        "            return false;\n"
        "        }\n"
        "        if (!SINGLE_SERVER_HOST.equals(sanitize(host)) || port != SINGLE_SERVER_PORT) {\n"
        "            return false;\n"
        "        }",
        "selected-server restriction",
    )
    manager = replace_once(
        manager,
        "        if (context == null || TextUtils.isEmpty(sanitizedHost) || !isValidPort(port)) {\n"
        "            return ServerOption.empty();\n"
        "        }",
        "        if (context == null || TextUtils.isEmpty(sanitizedHost) || !isValidPort(port)) {\n"
        "            return ServerOption.empty();\n"
        "        }\n"
        "        if (!SINGLE_SERVER_HOST.equals(sanitizedHost) || port != SINGLE_SERVER_PORT) {\n"
        "            return ServerOption.empty();\n"
        "        }\n"
        "        sanitizedName = SINGLE_SERVER_NAME;\n"
        "        favorite = true;",
        "add-server restriction",
    )
    remove_prefix = (
        "    public static boolean removeServer(Context context, ServerOption option) {\n"
        "        if (context == null || option == null || !option.isValid()) {\n"
        "            return false;\n"
        "        }"
    )
    remove_replacement = remove_prefix + (
        "\n        if (option.matches(SINGLE_SERVER_HOST, SINGLE_SERVER_PORT)) {\n"
        "            return false;\n"
        "        }"
    )
    manager = replace_once(manager, remove_prefix, remove_replacement, "fixed-server protection")
    manager_path.write_text(manager, encoding="utf-8")

    samp = samp_path.read_text(encoding="utf-8")
    on_create = (
        '    public void onCreate(Bundle savedInstanceState) {\n'
        '        Log.i(TAG, "**** onCreate");'
    )
    samp = replace_once(
        samp,
        on_create,
        on_create + "\n        instance = this;",
        "early SAMP activity instance",
    )
    samp = replace_once(
        samp,
        "        instance = this;\n        //WEBVIEW",
        "        //WEBVIEW",
        "remove late duplicate activity instance",
    )
    system_init = (
        "    @Override\n"
        "    protected boolean systemInit() {\n"
        "        boolean initialized = super.systemInit();\n"
        "        if (initialized) {\n"
        "            mJavaManager = new CefJavaManager(mAndroidUI, this);\n"
        "            mClientManager = new CefClientManager(this);\n"
        "            mJavaManager.setClientManager(mClientManager);\n"
        "            mClientManager.setJavaManager(mJavaManager);\n"
        "        }\n"
        "        return initialized;\n"
        "    }\n\n"
    )
    samp = replace_once(
        samp,
        "    @Override\n    public void onCreate(Bundle savedInstanceState) {",
        system_init + "    @Override\n    public void onCreate(Bundle savedInstanceState) {",
        "CEF Java/native initialization",
    )
    samp = replace_once(
        samp,
        "        CefJavaManager mJavaManager = null;\n"
        "        if (mJavaManager != null && mJavaManager.isShow()) {",
        "        if (mJavaManager != null && mJavaManager.isShow()) {",
        "CEF pause/resume manager field",
    )
    samp_path.write_text(samp, encoding="utf-8")

    gradle = gradle_path.read_text(encoding="utf-8")
    gradle = gradle.replace(
        'manifestPlaceholders = [appLabel: "News RP"]',
        f'manifestPlaceholders = [appLabel: "{SERVER_NAME}"]',
    )
    gradle_path.write_text(gradle, encoding="utf-8")

    if strings_path.exists():
        strings = strings_path.read_text(encoding="utf-8")
        strings = re.sub(
            r'(<string name="app_name">).*?(</string>)',
            rf"\g<1>{SERVER_NAME}\g<2>",
            strings,
            count=1,
        )
        strings_path.write_text(strings, encoding="utf-8")

    print(f"Configured {SERVER_NAME} at {SERVER_HOST}:{SERVER_PORT}")
    print("Initialized the included SA:MP Mobile CEF bridge for the GM's UCP flow.")


if __name__ == "__main__":
    main()
