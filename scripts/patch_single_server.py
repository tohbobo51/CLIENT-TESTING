#!/usr/bin/env python3
"""
patch_single_server.py
Applies Vice Side Roleplay single-server locking, local game-data extraction setup,
orientation locking, and signing configuration to the client repository.
"""

from pathlib import Path
import re
import sys

SERVER_HOST = "142.132.203.47"
SERVER_PORT = 10125
SERVER_NAME = "Vice Side Roleplay"

def replace_or_warn(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        print(f"[WARN] Text block for '{label}' not found, skipping specific replacement.", file=sys.stderr)
        return text
    return text.replace(old, new, 1)

def patch_settings_ini(root: Path) -> None:
    settings_ini = root / "app/src/main/assets/settings.ini"
    if settings_ini.exists():
        content = settings_ini.read_text(encoding="utf-8")
        content = re.sub(r"host\s*=\s*[^\r\n]+", f"host = {SERVER_HOST}", content)
        content = re.sub(r"port\s*=\s*[^\r\n]+", f"port = {SERVER_PORT}", content)
        settings_ini.write_text(content, encoding="utf-8")
        print(f"[*] Patched settings.ini -> host={SERVER_HOST}, port={SERVER_PORT}")

def patch_servers_json(root: Path) -> None:
    servers_json = root / "app/src/main/assets/servers.json"
    if servers_json.exists():
        servers_json.write_text('{\n  "servers": []\n}\n', encoding="utf-8")
        print("[*] Emptied servers.json")

def patch_update_sources(root: Path) -> None:
    update_sources = root / "app/src/main/assets/update_sources.json"
    if update_sources.exists():
        update_sources.write_text(
            '{\n  "client_config_urls": [],\n  "fallback_file_base_urls": [],\n  "huggingface": {\n    "repo_id": "",\n    "repo_type": "dataset",\n    "revision": "main",\n    "client_config_path": "",\n    "files_path_prefix": ""\n  },\n  "data_variants": []\n}\n',
            encoding="utf-8"
        )
        print("[*] Neutralized update_sources.json (removed external download endpoints)")

def patch_update_source_resolver(root: Path) -> None:
    resolver_path = root / "app/src/main/java/com/xyron/game/launcher/util/UpdateSourceResolver.java"
    if resolver_path.exists():
        code = resolver_path.read_text(encoding="utf-8")
        code = code.replace('"https://rp.goldcityrolrplay.space/dowloandoficial/client_config.json"', '""')
        code = code.replace('"https://rp.goldcityrolrplay.space/dowloandoficial/files"', '""')
        resolver_path.write_text(code, encoding="utf-8")
        print("[*] Neutralized hardcoded URLs in UpdateSourceResolver.java")

def patch_settings_fragment(root: Path) -> None:
    settings_fragment = root / "app/src/main/java/com/xyron/game/launcher/fragments/SettingsFragment.java"
    if settings_fragment.exists():
        code = settings_fragment.read_text(encoding="utf-8")
        old_block = (
            "        if (addServerButton != null) {\n"
            "            addServerButton.setOnTouchListener(new ButtonAnimator(getContext(), addServerButton));\n"
            "            addServerButton.setOnClickListener(v -> showAddServerDialog());\n"
            "        }"
        )
        new_block = (
            "        if (addServerButton != null) {\n"
            "            addServerButton.setVisibility(View.GONE);\n"
            "        }"
        )
        code = replace_or_warn(code, old_block, new_block, "hide addServerButton in SettingsFragment")
        settings_fragment.write_text(code, encoding="utf-8")
        print("[*] Updated SettingsFragment.java to hide add server button")

def patch_servers_fragment(root: Path) -> None:
    servers_fragment = root / "app/src/main/java/com/xyron/game/launcher/fragments/ServersFragment.java"
    if servers_fragment.exists():
        code = servers_fragment.read_text(encoding="utf-8")
        code = code.replace(
            "if (addServerShortcut != null) {\n            addServerShortcut.setVisibility(View.VISIBLE);\n        }",
            "if (addServerShortcut != null) {\n            addServerShortcut.setVisibility(View.GONE);\n        }"
        )
        code = code.replace(
            "if (removeAction != null) {",
            "if (removeAction != null) {\n            removeAction.setVisibility(View.GONE);"
        )
        servers_fragment.write_text(code, encoding="utf-8")
        print("[*] Updated ServersFragment.java to hide add/remove server actions")

def patch_manifest(root: Path) -> None:
    manifest_path = root / "app/src/main/AndroidManifest.xml"
    if manifest_path.exists():
        manifest = manifest_path.read_text(encoding="utf-8")
        manifest = manifest.replace('android:installLocation="auto"', 'android:installLocation="internalOnly"')
        manifest_path.write_text(manifest, encoding="utf-8")
        print("[*] Updated AndroidManifest.xml: installLocation='internalOnly'")

def patch_root_gradle(root: Path) -> None:
    root_gradle = root / "build.gradle"
    if root_gradle.exists():
        gradle_text = root_gradle.read_text(encoding="utf-8")
        gradle_text = gradle_text.replace("jcenter()", "mavenCentral()")
        root_gradle.write_text(gradle_text, encoding="utf-8")
        print("[*] Replaced jcenter() with mavenCentral() in root build.gradle")

def patch_samp_orientation(root: Path) -> None:
    samp_path = root / "app/src/main/java/com/xyron/game/main/SAMP.java"
    if samp_path.exists():
        code = samp_path.read_text(encoding="utf-8")
        pkg = "package com.xyron.game.main;\n"
        if "import android.content.pm.ActivityInfo;" not in code and pkg in code:
            code = code.replace(pkg, pkg + "import android.content.pm.ActivityInfo;\n", 1)
        
        target = "    public void onCreate(Bundle savedInstanceState) {\n        Log.i(TAG, \"**** onCreate\");"
        replacement = (
            "    public void onCreate(Bundle savedInstanceState) {\n"
            "        setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE);\n"
            "        Log.i(TAG, \"**** onCreate\");"
        )
        code = replace_or_warn(code, target, replacement, "SAMP onCreate landscape lock")
        samp_path.write_text(code, encoding="utf-8")
        print("[*] Added landscape lock to SAMP.java onCreate")

def patch_entry_activity(root: Path) -> None:
    entry_path = root / "app/src/main/java/com/xyron/game/launcher/EntryActivity.java"
    if not entry_path.exists():
        return

    new_content = """package com.xyron.game.launcher;

import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.ActivityInfo;
import android.content.res.AssetManager;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.TextUtils;
import android.util.Log;
import android.view.View;
import android.widget.TextView;
import com.google.android.material.progressindicator.LinearProgressIndicator;
import com.xyron.game.R;
import com.xyron.game.launcher.util.ButtonAnimator;
import com.xyron.game.launcher.util.ConfigValidator;
import com.xyron.game.launcher.util.GameDataVerifier;
import com.xyron.game.launcher.util.ServerConfigManager;
import org.ini4j.Wini;

import java.io.BufferedInputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

public class EntryActivity extends SampActivity {
    public static final String EXTRA_INITIAL_TAB = "initial_tab";
    public static final String EXTRA_FORCE_UPDATE_DATA = "force_update_data";
    private static final String EXTRA_NICKNAME = "nickname";
    private static final String TAG = "EntryActivity";
    private static final String PREF_NAME = "viceside_data";
    private static final String PREF_EXTRACTED = "extracted_v1";

    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private TextView statusTitle;
    private LinearProgressIndicator progressBar;
    private boolean isExtracting = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE);
        super.onCreate(savedInstanceState);

        ConfigValidator.validateConfigFiles(this);
        ServerConfigManager.ensureSelectedServer(this);
        applyIncomingConnection(getIntent());

        boolean forceUpdate = getIntent() != null
                && getIntent().getBooleanExtra(EXTRA_FORCE_UPDATE_DATA, false);

        SharedPreferences prefs = getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
        boolean alreadyExtracted = !forceUpdate && prefs.getBoolean(PREF_EXTRACTED, false)
                && GameDataVerifier.hasRequiredGameData(this);

        if (alreadyExtracted) {
            launchMainActivity();
            return;
        }

        setupExtractionUi();
        startDataExtraction();
    }

    private void setupExtractionUi() {
        setContentView(R.layout.activity_splash);
        statusTitle = findViewById(R.id.textView2);
        if (statusTitle != null) {
            statusTitle.setText("Menyiapkan Vice Side Roleplay...");
        }

        progressBar = findViewById(R.id.progressBar);
        if (progressBar == null) {
            progressBar = findViewById(R.id.progressBarBlue);
        }
        if (progressBar != null) {
            progressBar.setVisibility(View.VISIBLE);
            progressBar.setIndeterminate(false);
            progressBar.setProgress(0);
        }
    }

    private void startDataExtraction() {
        if (isExtracting) return;
        isExtracting = true;

        new Thread(() -> {
            try {
                File targetDir = getExternalFilesDir(null);
                if (targetDir == null) {
                    throw new IOException("Penyimpanan perangkat tidak dapat diakses.");
                }

                List<String> zipFiles = findGameDataZipAssets();
                if (zipFiles.isEmpty()) {
                    Log.w(TAG, "No game_data zip found in assets, checking existing data");
                    if (GameDataVerifier.hasRequiredGameData(this)) {
                        markExtractedAndProceed();
                        return;
                    }
                    throw new IOException("Arsip data game tidak ditemukan di dalam APK.");
                }

                int totalZips = zipFiles.size();
                for (int i = 0; i < totalZips; i++) {
                    String zipPath = zipFiles.get(i);
                    extractZipAsset(zipPath, targetDir, i, totalZips);
                }

                if (!GameDataVerifier.hasRequiredGameData(this)) {
                    throw new IOException("Verifikasi data game belum lengkap.");
                }

                markExtractedAndProceed();
            } catch (Exception e) {
                Log.e(TAG, "Extraction error", e);
                mainHandler.post(() -> showExtractionError(e.getMessage()));
            } finally {
                isExtracting = false;
            }
        }, "ViceSide-AssetExtractor").start();
    }

    private List<String> findGameDataZipAssets() {
        List<String> list = new ArrayList<>();
        AssetManager am = getAssets();
        try {
            String[] files = am.list("game_data");
            if (files != null && files.length > 0) {
                for (String f : files) {
                    if (f.endsWith(".zip")) {
                        list.add("game_data/" + f);
                    }
                }
            }
        } catch (IOException ignored) {}

        if (list.isEmpty()) {
            try {
                String[] rootFiles = am.list("");
                if (rootFiles != null) {
                    for (String f : rootFiles) {
                        if (f.endsWith(".zip")) {
                            list.add(f);
                        }
                    }
                }
            } catch (IOException ignored) {}
        }
        return list;
    }

    private void extractZipAsset(String assetPath, File destDir, int zipIndex, int totalZips) throws IOException {
        String fileName = new File(assetPath).getName();
        mainHandler.post(() -> {
            if (statusTitle != null) {
                statusTitle.setText("Mengekstrak " + fileName + " (" + (zipIndex + 1) + "/" + totalZips + ")...");
            }
        });

        byte[] buffer = new byte[65536];
        try (InputStream is = getAssets().open(assetPath);
             BufferedInputStream bis = new BufferedInputStream(is, 65536);
             ZipInputStream zis = new ZipInputStream(bis)) {

            ZipEntry entry;
            int count = 0;
            while ((entry = zis.getNextEntry()) != null) {
                String entryName = entry.getName();
                if (entryName == null) continue;
                String cleanPath = entryName;
                if (cleanPath.startsWith("files/")) {
                    cleanPath = cleanPath.substring(6);
                } else if (cleanPath.startsWith("/")) {
                    cleanPath = cleanPath.substring(1);
                }
                if (cleanPath.isEmpty()) continue;

                File targetFile = new File(destDir, cleanPath);
                if (entry.isDirectory()) {
                    targetFile.mkdirs();
                    continue;
                }

                long expectedSize = entry.getSize();
                if (targetFile.exists() && expectedSize > 0 && targetFile.length() == expectedSize) {
                    zis.closeEntry();
                    continue;
                }

                File parent = targetFile.getParentFile();
                if (parent != null && !parent.exists()) {
                    parent.mkdirs();
                }

                File partFile = new File(targetFile.getParentFile(), targetFile.getName() + ".part");
                try (FileOutputStream fos = new FileOutputStream(partFile)) {
                    int len;
                    while ((len = zis.read(buffer)) != -1) {
                        fos.write(buffer, 0, len);
                    }
                }

                if (partFile.exists()) {
                    if (targetFile.exists()) {
                        targetFile.delete();
                    }
                    partFile.renameTo(targetFile);
                }
                zis.closeEntry();

                count++;
                if (count % 25 == 0) {
                    final int currentProgress = (count % 100);
                    mainHandler.post(() -> {
                        if (progressBar != null) {
                            progressBar.setProgress(currentProgress);
                        }
                    });
                }
            }
        }
    }

    private void markExtractedAndProceed() {
        getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)
                .edit()
                .putBoolean(PREF_EXTRACTED, true)
                .apply();

        ConfigValidator.validateConfigFiles(this);
        mainHandler.post(this::launchMainActivity);
    }

    private void showExtractionError(String errorMsg) {
        if (statusTitle != null) {
            statusTitle.setText("Gagal mengekstrak data game.");
        }
        View dialogView = getLayoutInflater().inflate(R.layout.dialog_update_prompt, null, false);
        TextView titleView = dialogView.findViewById(R.id.update_prompt_title);
        TextView bodyView = dialogView.findViewById(R.id.update_prompt_body);
        TextView primaryButton = dialogView.findViewById(R.id.update_prompt_primary);
        TextView secondaryButton = dialogView.findViewById(R.id.update_prompt_secondary);

        if (titleView != null) titleView.setText("Ekstraksi Gagal");
        if (bodyView != null) {
            bodyView.setText("Terjadi kendala saat mengekstrak data game lokal:\\n"
                    + (errorMsg != null ? errorMsg : "Sisa ruang penyimpanan tidak cukup.")
                    + "\\nPastikan tersedia ruang kosong minimal 4 GB.");
        }
        if (primaryButton != null) {
            primaryButton.setText("Coba Lagi");
            primaryButton.setOnTouchListener(new ButtonAnimator(this, primaryButton));
        }
        if (secondaryButton != null) {
            secondaryButton.setText("Keluar");
            secondaryButton.setOnTouchListener(new ButtonAnimator(this, secondaryButton));
        }

        AlertDialog dialog = new AlertDialog.Builder(this)
                .setView(dialogView)
                .setCancelable(false)
                .create();

        if (dialog.getWindow() != null) {
            dialog.getWindow().setBackgroundDrawable(new ColorDrawable(Color.TRANSPARENT));
        }

        if (primaryButton != null) {
            primaryButton.setOnClickListener(v -> {
                dialog.dismiss();
                setupExtractionUi();
                startDataExtraction();
            });
        }
        if (secondaryButton != null) {
            secondaryButton.setOnClickListener(v -> {
                dialog.dismiss();
                finish();
            });
        }
        dialog.show();
    }

    private void launchMainActivity() {
        Intent gameIntent = new Intent(this, MainActivity.class);
        if (getIntent() != null && getIntent().getExtras() != null) {
            gameIntent.putExtras(getIntent().getExtras());
        }
        gameIntent.addFlags(Intent.FLAG_ACTIVITY_NO_ANIMATION);
        startActivity(gameIntent);
        overridePendingTransition(0, 0);
        finish();
    }

    private void applyIncomingConnection(Intent intent) {
        if (intent == null) return;
        String nickname = sanitize(intent.getStringExtra(EXTRA_NICKNAME));
        if (!TextUtils.isEmpty(nickname)) {
            saveNickname(nickname);
        }
    }

    private void saveNickname(String nickname) {
        File settingsFile = new File(getExternalFilesDir(null), "SAMP/settings.ini");
        File parent = settingsFile.getParentFile();
        if (parent != null && !parent.exists() && !parent.mkdirs()) {
            return;
        }
        try {
            if (!settingsFile.exists() && !settingsFile.createNewFile()) {
                return;
            }
            Wini wini = new Wini(settingsFile);
            wini.put("client", "name", nickname);
            wini.store();
        } catch (IOException e) {
            Log.e(TAG, "Could not save nickname", e);
        }
    }

    private String sanitize(String value) {
        return value == null ? "" : value.trim();
    }
}
"""
    entry_path.write_text(new_content, encoding="utf-8")
    print("[*] Replaced EntryActivity.java with first-run asset extractor & orientation lock")

def patch_app_gradle(root: Path) -> None:
    app_gradle = root / "app/build.gradle"
    if not app_gradle.exists():
        return

    app_text = app_gradle.read_text(encoding="utf-8")

    # Dynamic versionCode
    app_text = re.sub(
        r"versionCode\s+\d+",
        "versionCode (System.getenv('BUILD_VERSION_CODE') ? Integer.parseInt(System.getenv('BUILD_VERSION_CODE')) : 1001)",
        app_text
    )

    # androidResources { noCompress 'zip' }, sourceSets, and signingConfigs
    if "noCompress 'zip'" not in app_text:
        insert_pos = app_text.find("buildTypes {")
        if insert_pos != -1:
            resource_block = (
                "    androidResources {\n"
                "        noCompress 'zip'\n"
                "    }\n\n"
                "    sourceSets {\n"
                "        main {\n"
                "            assets.srcDirs += ['game-data']\n"
                "        }\n"
                "    }\n\n"
                "    signingConfigs {\n"
                "        release {\n"
                "            storeFile file(System.getenv('KEYSTORE_PATH') ?: (project.findProperty('KEYSTORE_FILE') ?: 'release.keystore'))\n"
                "            storePassword System.getenv('KEYSTORE_PASSWORD') ?: (project.findProperty('KEYSTORE_PASSWORD') ?: '')\n"
                "            keyAlias System.getenv('KEY_ALIAS') ?: (project.findProperty('KEY_ALIAS') ?: '')\n"
                "            keyPassword System.getenv('KEY_PASSWORD') ?: (System.getenv('KEYSTORE_PASSWORD') ?: (project.findProperty('KEY_PASSWORD') ?: (project.findProperty('KEYSTORE_PASSWORD') ?: '')))\n"
                "        }\n"
                "    }\n\n"
            )
            app_text = app_text[:insert_pos] + resource_block + app_text[insert_pos:]

    # Enable signing in release buildType
    app_text = re.sub(
        r"//signingConfig\s+signingConfigs\.release",
        "signingConfig signingConfigs.release",
        app_text
    )
    app_gradle.write_text(app_text, encoding="utf-8")
    print("[*] Configured app/build.gradle (signingConfigs.release, noCompress 'zip', game-data sourceSet, dynamic versionCode)")

def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "client").resolve()
    print(f"Applying patch_single_server to: {root}")

    patch_settings_ini(root)
    patch_servers_json(root)
    patch_update_sources(root)
    patch_update_source_resolver(root)
    patch_settings_fragment(root)
    patch_servers_fragment(root)
    patch_manifest(root)
    patch_root_gradle(root)
    patch_samp_orientation(root)
    patch_entry_activity(root)
    patch_app_gradle(root)

    print("[SUCCESS] All single-server, CEF, and asset extraction patches applied successfully.")

if __name__ == "__main__":
    main()
