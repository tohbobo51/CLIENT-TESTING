#!/usr/bin/env python3
"""
patch_single_server.py
Applies Vice Side Roleplay single-server locking, client-side manifest-based data download,
manual import from Documents/SampMobile/, orientation locking, and signing configuration.
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

def patch_gradle_properties(root: Path) -> None:
    prop_path = root / "gradle.properties"
    if prop_path.exists():
        text = prop_path.read_text(encoding="utf-8")
        text = re.sub(r"org\.gradle\.jvmargs\s*=\s*[^\r\n]+", "org.gradle.jvmargs=-Xmx8192m -XX:MaxMetaspaceSize=1024m -Dfile.encoding=UTF-8", text)
        prop_path.write_text(text, encoding="utf-8")
        print("[*] Configured gradle.properties JVM args: -Xmx8192m")

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

def patch_splash_layout(root: Path) -> None:
    layout_path = root / "app/src/main/res/layout/activity_splash.xml"
    if not layout_path.exists():
        return

    splash_layout_content = """<?xml version="1.0" encoding="utf-8"?>
<androidx.constraintlayout.widget.ConstraintLayout xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:id="@+id/main_splash_layout"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="@drawable/bg_red">

    <View
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:background="@drawable/home_overlay" />

    <LinearLayout
        android:layout_width="600dp"
        android:layout_height="wrap_content"
        android:background="@drawable/launcher_hero_panel"
        android:elevation="12dp"
        android:gravity="center_horizontal"
        android:orientation="vertical"
        android:padding="24dp"
        app:layout_constraintBottom_toBottomOf="parent"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintTop_toTopOf="parent">

        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:gravity="center_vertical"
            android:orientation="horizontal">

            <FrameLayout
                android:layout_width="80dp"
                android:layout_height="80dp"
                android:background="@drawable/launcher_logo_frame"
                android:padding="12dp">

                <ImageView
                    android:id="@+id/imageView"
                    android:layout_width="match_parent"
                    android:layout_height="match_parent"
                    android:scaleType="fitCenter"
                    app:srcCompat="@drawable/news_rp_logo" />
            </FrameLayout>

            <LinearLayout
                android:layout_width="0dp"
                android:layout_height="wrap_content"
                android:layout_marginStart="16dp"
                android:layout_weight="1"
                android:orientation="vertical">

                <TextView
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:background="@drawable/home_news_badge"
                    android:fontFamily="@font/montserrat_bold"
                    android:paddingStart="10dp"
                    android:paddingTop="4dp"
                    android:paddingEnd="10dp"
                    android:paddingBottom="4dp"
                    android:text="Pembaruan Data Game"
                    android:textAllCaps="true"
                    android:textColor="@android:color/white"
                    android:textSize="9sp" />

                <TextView
                    android:id="@+id/textView2"
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:layout_marginTop="6dp"
                    android:fontFamily="@font/montserrat_black"
                    android:text="Menyiapkan Vice Side Roleplay..."
                    android:textColor="@android:color/white"
                    android:textSize="18sp" />

                <TextView
                    android:id="@+id/statusSubtitle"
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:layout_marginTop="4dp"
                    android:fontFamily="@font/montserrat_medium"
                    android:text="Memeriksa pembaruan data game..."
                    android:textColor="#D7CDE1"
                    android:textSize="11sp" />
            </LinearLayout>
        </LinearLayout>

        <com.google.android.material.progressindicator.LinearProgressIndicator
            android:id="@+id/progressBar"
            android:layout_width="match_parent"
            android:layout_height="12dp"
            android:layout_marginTop="16dp"
            android:indeterminate="false"
            android:visibility="visible"
            app:indicatorColor="#FBBF23"
            app:trackColor="#20FFFFFF"
            app:trackCornerRadius="999dp"
            app:trackThickness="12dp" />

        <TextView
            android:id="@+id/statusInstructions"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:layout_marginTop="12dp"
            android:fontFamily="@font/montserrat_medium"
            android:gravity="center"
            android:text="Impor manual ZArchiver: Salin/ekstrak CRMP.zip ke /storage/emulated/0/Documents/SampMobile/"
            android:textColor="#B0A4C0"
            android:textSize="10sp" />

        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:layout_marginTop="16dp"
            android:gravity="center"
            android:orientation="horizontal">

            <TextView
                android:id="@+id/btnCancel"
                android:layout_width="0dp"
                android:layout_height="42dp"
                android:layout_marginEnd="6dp"
                android:layout_weight="1"
                android:background="@drawable/home_action_text_button"
                android:fontFamily="@font/montserrat_bold"
                android:gravity="center"
                android:text="Batal / Jeda"
                android:textAllCaps="true"
                android:textColor="@android:color/white"
                android:textSize="11sp" />

            <TextView
                android:id="@+id/btnImport"
                android:layout_width="0dp"
                android:layout_height="42dp"
                android:layout_marginStart="6dp"
                android:layout_marginEnd="6dp"
                android:layout_weight="1.3"
                android:background="@drawable/launcher_cta_gold"
                android:fontFamily="@font/montserrat_black"
                android:gravity="center"
                android:text="Impor dari Folder"
                android:textAllCaps="true"
                android:textColor="#24120A"
                android:textSize="11sp" />

            <TextView
                android:id="@+id/btnCopyPath"
                android:layout_width="0dp"
                android:layout_height="42dp"
                android:layout_marginStart="6dp"
                android:layout_weight="1"
                android:background="@drawable/home_action_text_button"
                android:fontFamily="@font/montserrat_bold"
                android:gravity="center"
                android:text="Salin Jalur"
                android:textAllCaps="true"
                android:textColor="@android:color/white"
                android:textSize="11sp" />
        </LinearLayout>
    </LinearLayout>
</androidx.constraintlayout.widget.ConstraintLayout>
"""
    layout_path.write_text(splash_layout_content, encoding="utf-8")
    print("[*] Replaced activity_splash.xml with updater & manual import layout")

def patch_entry_activity(root: Path) -> None:
    entry_path = root / "app/src/main/java/com/xyron/game/launcher/EntryActivity.java"
    if not entry_path.exists():
        return

    new_content = """package com.xyron.game.launcher;

import android.app.AlertDialog;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.ActivityInfo;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.TextUtils;
import android.util.Log;
import android.view.View;
import android.widget.TextView;
import android.widget.Toast;

import com.downloader.Error;
import com.downloader.OnCancelListener;
import com.downloader.OnDownloadListener;
import com.downloader.OnPauseListener;
import com.downloader.OnProgressListener;
import com.downloader.OnStartOrResumeListener;
import com.downloader.PRDownloader;
import com.downloader.PRDownloaderConfig;
import com.downloader.Progress;
import com.downloader.database.DownloadModel;
import com.downloader.internal.ComponentHolder;
import com.downloader.utils.Utils;
import com.google.android.material.progressindicator.LinearProgressIndicator;
import com.xyron.game.R;
import com.xyron.game.launcher.util.ButtonAnimator;
import com.xyron.game.launcher.util.ConfigValidator;
import com.xyron.game.launcher.util.GameDataVerifier;
import com.xyron.game.launcher.util.ServerConfigManager;
import org.ini4j.Wini;
import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedInputStream;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

public class EntryActivity extends SampActivity {
    public static final String EXTRA_INITIAL_TAB = "initial_tab";
    public static final String EXTRA_FORCE_UPDATE_DATA = "force_update_data";
    private static final String EXTRA_NICKNAME = "nickname";
    private static final String TAG = "ViceSide-Entry";
    private static final String PREF_NAME = "viceside_data";
    private static final String PREF_MANIFEST_VERSION = "manifest_version";
    private static final String PREF_INSTALLED_SHA_PREFIX = "installed_sha256_";

    public static final String PRIMARY_MANIFEST_URL =
            "https://github.com/tohbobo51/samp-game-data/releases/latest/download/data-manifest.json";
    public static final String FALLBACK_MANIFEST_URL =
            "https://raw.githubusercontent.com/tohbobo51/samp-game-data/main/data-manifest.json";
    public static final String MANUAL_IMPORT_PATH =
            "/storage/emulated/0/Documents/SampMobile/";

    public static class ManifestFile {
        public final String id;
        public final String url;
        public final long size;
        public final String sha256;
        public final String extractTo;
        public final String fileName;

        public ManifestFile(String id, String url, long size, String sha256, String extractTo) {
            this.id = id;
            this.url = url;
            this.size = size;
            this.sha256 = sha256;
            this.extractTo = extractTo;
            String computedName = null;
            try {
                String path = new URL(url).getPath();
                if (path != null && path.contains("/")) {
                    computedName = path.substring(path.lastIndexOf('/') + 1);
                }
            } catch (Exception ignored) {}
            if (TextUtils.isEmpty(computedName)) {
                computedName = id + ".zip";
            }
            this.fileName = computedName;
        }
    }

    public static class ManifestData {
        public final int version;
        public final String title;
        public final List<ManifestFile> files = new ArrayList<>();

        public ManifestData(int version, String title) {
            this.version = version;
            this.title = title;
        }
    }

    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private TextView statusTitle;
    private TextView statusSubtitle;
    private TextView statusInstructions;
    private TextView btnCancel;
    private TextView btnImport;
    private TextView btnCopyPath;
    private LinearProgressIndicator progressBar;

    private ManifestData currentManifest;
    private final List<ManifestFile> pendingFilesToDownload = new ArrayList<>();
    private int activeDownloadId = -1;
    private boolean isPaused = false;
    private boolean isFlowBusy = false;

    private long lastSpeedTime = 0;
    private long lastSpeedBytes = 0;
    private String lastSpeedText = "0 KB/s";
    private String lastEtaText = "--:--";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE);
        super.onCreate(savedInstanceState);

        ConfigValidator.validateConfigFiles(this);
        ServerConfigManager.ensureSelectedServer(this);
        applyIncomingConnection(getIntent());

        PRDownloader.initialize(getApplicationContext(),
                PRDownloaderConfig.newBuilder()
                        .setDatabaseEnabled(true)
                        .setReadTimeout(30000)
                        .setConnectTimeout(30000)
                        .build());

        setupUi();
        startUpdateFlow();
    }

    private void setupUi() {
        setContentView(R.layout.activity_splash);
        statusTitle = findViewById(R.id.textView2);
        statusSubtitle = findViewById(R.id.statusSubtitle);
        statusInstructions = findViewById(R.id.statusInstructions);
        btnCancel = findViewById(R.id.btnCancel);
        btnImport = findViewById(R.id.btnImport);
        btnCopyPath = findViewById(R.id.btnCopyPath);

        progressBar = findViewById(R.id.progressBar);
        if (progressBar == null) {
            progressBar = findViewById(R.id.progressBarBlue);
        }
        if (progressBar != null) {
            progressBar.setVisibility(View.VISIBLE);
            progressBar.setIndeterminate(true);
        }

        if (statusTitle != null) {
            statusTitle.setText("Menyiapkan Vice Side Roleplay...");
        }
        if (statusSubtitle != null) {
            statusSubtitle.setText("Memeriksa status data game...");
        }
        if (statusInstructions != null) {
            statusInstructions.setText("Jalur impor manual: " + MANUAL_IMPORT_PATH);
        }

        if (btnCancel != null) {
            btnCancel.setOnTouchListener(new ButtonAnimator(this, btnCancel));
            btnCancel.setOnClickListener(v -> onCancelOrPauseClicked());
        }
        if (btnImport != null) {
            btnImport.setOnTouchListener(new ButtonAnimator(this, btnImport));
            btnImport.setOnClickListener(v -> onManualImportClicked());
        }
        if (btnCopyPath != null) {
            btnCopyPath.setOnTouchListener(new ButtonAnimator(this, btnCopyPath));
            btnCopyPath.setOnClickListener(v -> onCopyPathClicked());
        }
    }

    private void startUpdateFlow() {
        if (isFlowBusy) return;
        isFlowBusy = true;

        new Thread(() -> {
            try {
                boolean forceUpdate = getIntent() != null
                        && getIntent().getBooleanExtra(EXTRA_FORCE_UPDATE_DATA, false);

                mainHandler.post(() -> {
                    if (statusSubtitle != null) statusSubtitle.setText("Mengambil manifest rilis data...");
                    if (progressBar != null) progressBar.setIndeterminate(true);
                });

                String manifestJson = fetchManifestJson();
                if (manifestJson == null) {
                    SharedPreferences prefs = getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
                    if (!forceUpdate && prefs.getInt(PREF_MANIFEST_VERSION, -1) > 0
                            && GameDataVerifier.hasRequiredGameData(this)) {
                        Log.i(TAG, "Offline mode: manifest fetch failed but game data verified.");
                        markReadyAndProceed();
                        return;
                    }
                    throw new IOException("Koneksi internet gagal dan data belum terpasang.");
                }

                ManifestData manifest = parseManifest(manifestJson);
                if (manifest == null || manifest.files.isEmpty()) {
                    throw new IOException("Format manifest data tidak valid.");
                }
                currentManifest = manifest;

                File downloadDir = new File(getExternalFilesDir(null), "downloads");
                if (!downloadDir.exists()) downloadDir.mkdirs();
                cleanObsoleteFiles(downloadDir, manifest);

                SharedPreferences prefs = getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
                int installedVersion = prefs.getInt(PREF_MANIFEST_VERSION, -1);

                if (!forceUpdate && installedVersion == manifest.version
                        && GameDataVerifier.hasRequiredGameData(this)) {
                    Log.i(TAG, "Data game sudah terpasang dan sesuai manifest versi " + manifest.version);
                    mainHandler.post(() -> {
                        if (statusTitle != null) statusTitle.setText("Data sudah terpasang");
                        if (statusSubtitle != null) statusSubtitle.setText("Memulai permainan...");
                    });
                    markReadyAndProceed();
                    return;
                }

                checkFilesAndPrepareQueue(manifest, downloadDir);
            } catch (Exception e) {
                Log.e(TAG, "Update flow error", e);
                mainHandler.post(() -> showErrorDialog(e.getMessage()));
            } finally {
                isFlowBusy = false;
            }
        }, "ViceSide-UpdateFlow").start();
    }

    private void checkFilesAndPrepareQueue(ManifestData manifest, File downloadDir) {
        File targetDir = getExternalFilesDir(null);
        SharedPreferences prefs = getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
        pendingFilesToDownload.clear();

        for (ManifestFile mf : manifest.files) {
            String installedSha = prefs.getString(PREF_INSTALLED_SHA_PREFIX + mf.id, "");
            if (installedSha.equalsIgnoreCase(mf.sha256) && GameDataVerifier.hasRequiredGameData(this)) {
                Log.i(TAG, "File " + mf.fileName + " sudah terpasang dengan sha256 cocok, melewati unduhan.");
                continue;
            }

            File finalFile = new File(downloadDir, mf.fileName);
            if (finalFile.exists() && finalFile.length() == mf.size) {
                mainHandler.post(() -> {
                    if (statusSubtitle != null) statusSubtitle.setText("Memverifikasi berkas lokal: " + mf.fileName);
                });
                String hash = calculateSha256(finalFile);
                if (hash.equalsIgnoreCase(mf.sha256)) {
                    Log.i(TAG, "Berkas lokal " + mf.fileName + " valid. Mengekstrak...");
                    try {
                        extractZip(finalFile, targetDir);
                        prefs.edit().putString(PREF_INSTALLED_SHA_PREFIX + mf.id, mf.sha256).apply();
                        continue;
                    } catch (IOException e) {
                        Log.e(TAG, "Ekstraksi berkas lokal gagal", e);
                    }
                } else {
                    Log.w(TAG, "Berkas lokal " + mf.fileName + " checksum tidak cocok. Dihapus.");
                    finalFile.delete();
                }
            }

            pendingFilesToDownload.add(mf);
        }

        if (pendingFilesToDownload.isEmpty()) {
            if (GameDataVerifier.hasRequiredGameData(this)) {
                prefs.edit().putInt(PREF_MANIFEST_VERSION, manifest.version).apply();
                markReadyAndProceed();
                return;
            } else {
                Log.w(TAG, "Semua file manifest tercatat terpasang tapi GameDataVerifier gagal. Melakukan unduh ulang.");
                pendingFilesToDownload.addAll(manifest.files);
            }
        }

        mainHandler.post(this::downloadNextPendingFile);
    }

    private void downloadNextPendingFile() {
        if (pendingFilesToDownload.isEmpty()) {
            finalizeInstallation();
            return;
        }

        ManifestFile currentFile = pendingFilesToDownload.get(0);
        File downloadDir = new File(getExternalFilesDir(null), "downloads");
        if (!downloadDir.exists()) downloadDir.mkdirs();

        String partFileName = currentFile.fileName + ".part";
        File partFile = new File(downloadDir, partFileName);
        File tempFile = new File(downloadDir, partFileName + ".temp");
        File finalFile = new File(downloadDir, currentFile.fileName);

        if (partFile.exists() && !tempFile.exists()) {
            partFile.renameTo(tempFile);
        }

        long initialOffset = tempFile.exists() ? tempFile.length() : 0L;
        int downloadId = Utils.getUniqueId(currentFile.url, downloadDir.getAbsolutePath(), partFileName);

        if (initialOffset > 0) {
            DownloadModel model = ComponentHolder.getInstance().getDbHelper().find(downloadId);
            if (model == null) {
                model = new DownloadModel();
                model.setId(downloadId);
                model.setUrl(currentFile.url);
                model.setDirPath(downloadDir.getAbsolutePath());
                model.setFileName(partFileName);
                model.setTotalBytes(currentFile.size);
                model.setDownloadedBytes(initialOffset);
                model.setLastModifiedAt(System.currentTimeMillis());
                ComponentHolder.getInstance().getDbHelper().insert(model);
            } else {
                model.setDownloadedBytes(initialOffset);
                ComponentHolder.getInstance().getDbHelper().update(model);
            }
        }

        Log.i(TAG, "[Download] Starting download for " + currentFile.fileName
                + " at offset: " + initialOffset + " / " + currentFile.size);

        lastSpeedTime = System.currentTimeMillis();
        lastSpeedBytes = initialOffset;
        isPaused = false;
        if (btnCancel != null) btnCancel.setText("Batal / Jeda");

        mainHandler.post(() -> {
            if (statusTitle != null) {
                statusTitle.setText("Mengunduh " + currentFile.fileName + "...");
            }
            if (progressBar != null) {
                progressBar.setIndeterminate(false);
                int pct = (int) ((initialOffset * 100) / (currentFile.size > 0 ? currentFile.size : 1));
                progressBar.setProgress(pct);
            }
        });

        activeDownloadId = PRDownloader.download(currentFile.url, downloadDir.getAbsolutePath(), partFileName)
                .build()
                .setOnStartOrResumeListener(new OnStartOrResumeListener() {
                    @Override
                    public void onStartOrResume() {
                        long currentOffset = tempFile.exists() ? tempFile.length() : 0L;
                        Log.i(TAG, "[Download] Download started/resumed for " + currentFile.fileName
                                + ", active offset: " + currentOffset);
                    }
                })
                .setOnProgressListener(new OnProgressListener() {
                    @Override
                    public void onProgress(Progress progress) {
                        onProgressUpdate(currentFile, progress.currentBytes, progress.totalBytes);
                    }
                })
                .setOnPauseListener(new OnPauseListener() {
                    @Override
                    public void onPause() {
                        long pausedOffset = tempFile.exists() ? tempFile.length() : 0L;
                        Log.i(TAG, "[Download] Download paused for " + currentFile.fileName
                                + " at byte: " + pausedOffset);
                    }
                })
                .setOnCancelListener(new OnCancelListener() {
                    @Override
                    public void onCancel() {
                        Log.i(TAG, "[Download] Download cancelled for " + currentFile.fileName);
                    }
                })
                .start(new OnDownloadListener() {
                    @Override
                    public void onDownloadComplete() {
                        onDownloadFinished(currentFile, partFile, finalFile);
                    }

                    @Override
                    public void onError(Error error) {
                        onDownloadFailed(currentFile, error);
                    }
                });
    }

    private void onProgressUpdate(ManifestFile item, long currentBytes, long totalBytes) {
        long now = System.currentTimeMillis();
        if (now - lastSpeedTime >= 800) {
            long timeDelta = now - lastSpeedTime;
            long bytesDelta = currentBytes - lastSpeedBytes;
            if (timeDelta > 0 && bytesDelta >= 0) {
                double bytesPerSec = (bytesDelta * 1000.0) / timeDelta;
                if (bytesPerSec >= 1048576) {
                    lastSpeedText = String.format(Locale.US, "%.1f MB/s", bytesPerSec / 1048576.0);
                } else {
                    lastSpeedText = String.format(Locale.US, "%.0f KB/s", bytesPerSec / 1024.0);
                }
                if (bytesPerSec > 0 && totalBytes > currentBytes) {
                    long remainingSec = (long) ((totalBytes - currentBytes) / bytesPerSec);
                    long mins = remainingSec / 60;
                    long secs = remainingSec % 60;
                    lastEtaText = String.format(Locale.US, "%02d:%02d", mins, secs);
                } else {
                    lastEtaText = "--:--";
                }
            }
            lastSpeedTime = now;
            lastSpeedBytes = currentBytes;
        }

        int percent = (int) ((currentBytes * 100) / (totalBytes > 0 ? totalBytes : 1));
        mainHandler.post(() -> {
            if (progressBar != null) {
                progressBar.setProgress(percent);
            }
            if (statusSubtitle != null) {
                double curMB = currentBytes / 1048576.0;
                double totMB = totalBytes / 1048576.0;
                statusSubtitle.setText(String.format(Locale.US,
                        "%s (%.1f / %.1f MB) • %d%% • %s • ETA: %s",
                        item.fileName, curMB, totMB, percent, lastSpeedText, lastEtaText));
            }
        });
    }

    private void onDownloadFinished(ManifestFile currentFile, File partFile, File finalFile) {
        activeDownloadId = -1;
        new Thread(() -> {
            try {
                mainHandler.post(() -> {
                    if (statusTitle != null) {
                        statusTitle.setText("Memverifikasi integritas (" + currentFile.fileName + ")...");
                    }
                    if (statusSubtitle != null) {
                        statusSubtitle.setText("Menghitung checksum SHA-256...");
                    }
                    if (progressBar != null) {
                        progressBar.setIndeterminate(true);
                    }
                });

                String sha256 = calculateSha256(partFile);
                if (!sha256.equalsIgnoreCase(currentFile.sha256)) {
                    Log.e(TAG, "[Download] Checksum mismatch for " + currentFile.fileName
                            + ": expected " + currentFile.sha256 + ", got " + sha256);
                    partFile.delete();
                    throw new IOException("Checksum berkas tidak cocok. Berkas korup atau tidak lengkap.");
                }

                Log.i(TAG, "[Download] Checksum verified: " + currentFile.fileName);
                if (finalFile.exists()) finalFile.delete();
                boolean renamed = partFile.renameTo(finalFile);
                if (!renamed) {
                    moveOrCopyFile(partFile, finalFile);
                }

                extractZip(finalFile, getExternalFilesDir(null));

                SharedPreferences prefs = getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
                prefs.edit().putString(PREF_INSTALLED_SHA_PREFIX + currentFile.id, currentFile.sha256).apply();

                if (!pendingFilesToDownload.isEmpty()) {
                    pendingFilesToDownload.remove(0);
                }

                if (pendingFilesToDownload.isEmpty()) {
                    finalizeInstallation();
                } else {
                    mainHandler.post(this::downloadNextPendingFile);
                }
            } catch (Exception e) {
                Log.e(TAG, "Error handling completed download", e);
                mainHandler.post(() -> showErrorDialog("Gagal memproses unduhan:\\n" + e.getMessage()));
            }
        }, "ViceSide-VerifyExtract").start();
    }

    private void onDownloadFailed(ManifestFile currentFile, Error error) {
        activeDownloadId = -1;
        Log.e(TAG, "[Download] Error downloading " + currentFile.fileName
                + ": " + (error != null ? error.getServerErrorMessage() : "unknown"));
        mainHandler.post(() -> {
            String msg = "Gagal mengunduh " + currentFile.fileName + ".";
            if (error != null && error.getResponseCode() != 0) {
                msg += " (HTTP " + error.getResponseCode() + ")";
            }
            showErrorDialog(msg + "\\nPeriksa koneksi internet Anda lalu coba lagi.");
        });
    }

    private void finalizeInstallation() {
        if (GameDataVerifier.hasRequiredGameData(this)) {
            if (currentManifest != null) {
                getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)
                        .edit()
                        .putInt(PREF_MANIFEST_VERSION, currentManifest.version)
                        .apply();
            }
            Log.i(TAG, "Game data verification passed! Launching MainActivity.");
            markReadyAndProceed();
        } else {
            Log.e(TAG, "Game data verification failed after extraction.");
            mainHandler.post(() -> showErrorDialog("Verifikasi data game tidak lengkap. Pastikan seluruh berkas terpasang."));
        }
    }

    private void onCancelOrPauseClicked() {
        if (activeDownloadId != -1) {
            if (!isPaused) {
                PRDownloader.pause(activeDownloadId);
                isPaused = true;
                if (btnCancel != null) btnCancel.setText("Lanjutkan");
                if (statusSubtitle != null) {
                    statusSubtitle.setText("Unduhan dijeda. Posisi byte tersimpan.");
                }
            } else {
                PRDownloader.resume(activeDownloadId);
                isPaused = false;
                if (btnCancel != null) btnCancel.setText("Batal / Jeda");
                if (statusSubtitle != null) {
                    statusSubtitle.setText("Melanjutkan unduhan...");
                }
            }
        } else {
            finish();
        }
    }

    private void onCopyPathClicked() {
        ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        if (clipboard != null) {
            ClipData clip = ClipData.newPlainText("Jalur Impor Data Game", MANUAL_IMPORT_PATH);
            clipboard.setPrimaryClip(clip);
            Toast.makeText(this, "Jalur disalin: " + MANUAL_IMPORT_PATH, Toast.LENGTH_LONG).show();
        }
    }

    private void onManualImportClicked() {
        if (activeDownloadId != -1) {
            PRDownloader.pause(activeDownloadId);
            isPaused = true;
            if (btnCancel != null) btnCancel.setText("Lanjutkan");
        }

        new Thread(() -> {
            File importDir = new File(MANUAL_IMPORT_PATH);
            if (!importDir.exists()) {
                importDir.mkdirs();
                mainHandler.post(() -> Toast.makeText(this,
                        "Folder belum berisi file. Salin CRMP.zip ke " + MANUAL_IMPORT_PATH,
                        Toast.LENGTH_LONG).show());
                return;
            }

            mainHandler.post(() -> {
                if (statusTitle != null) statusTitle.setText("Memeriksa folder impor manual...");
                if (statusSubtitle != null) statusSubtitle.setText("Menelusuri " + MANUAL_IMPORT_PATH);
                if (progressBar != null) progressBar.setIndeterminate(true);
            });

            if (currentManifest == null) {
                String manifestJson = fetchManifestJson();
                if (manifestJson != null) currentManifest = parseManifest(manifestJson);
            }

            if (currentManifest == null) {
                mainHandler.post(() -> showErrorDialog("Tidak dapat memuat manifest data untuk verifikasi impor."));
                return;
            }

            File targetDir = getExternalFilesDir(null);
            File downloadDir = new File(getExternalFilesDir(null), "downloads");
            if (!downloadDir.exists()) downloadDir.mkdirs();

            int importedCount = 0;
            List<String> mismatchList = new ArrayList<>();
            SharedPreferences prefs = getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);

            for (ManifestFile mf : currentManifest.files) {
                File candidateFile = new File(importDir, mf.fileName);
                if (!candidateFile.exists()) {
                    candidateFile = new File(importDir, mf.id + ".zip");
                }

                if (candidateFile.exists()) {
                    mainHandler.post(() -> {
                        if (statusSubtitle != null) {
                            statusSubtitle.setText("Memverifikasi SHA-256: " + candidateFile.getName());
                        }
                    });

                    if (candidateFile.length() != mf.size) {
                        mismatchList.add(candidateFile.getName() + " (ukuran tidak cocok)");
                        continue;
                    }

                    String sha = calculateSha256(candidateFile);
                    if (sha.equalsIgnoreCase(mf.sha256)) {
                        mainHandler.post(() -> {
                            if (statusSubtitle != null) {
                                statusSubtitle.setText("Mengimpor dan mengekstrak: " + candidateFile.getName());
                            }
                        });
                        File destFile = new File(downloadDir, mf.fileName);
                        moveOrCopyFile(candidateFile, destFile);
                        try {
                            extractZip(destFile, targetDir);
                            prefs.edit().putString(PREF_INSTALLED_SHA_PREFIX + mf.id, mf.sha256).apply();
                            importedCount++;
                        } catch (IOException e) {
                            Log.e(TAG, "Ekstraksi berkas impor gagal", e);
                        }
                    } else {
                        mismatchList.add(candidateFile.getName() + " (checksum berbeda)");
                    }
                }
            }

            File importTexdb = new File(importDir, "texdb");
            File importModels = new File(importDir, "models");
            if (importTexdb.exists() && importModels.exists()) {
                mainHandler.post(() -> {
                    if (statusSubtitle != null) statusSubtitle.setText("Mengimpor struktur folder terekstrak...");
                });
                copyDirectory(importDir, targetDir);
            }

            final int finalImported = importedCount;
            mainHandler.post(() -> {
                if (GameDataVerifier.hasRequiredGameData(this)) {
                    prefs.edit().putInt(PREF_MANIFEST_VERSION, currentManifest.version).apply();
                    Toast.makeText(this, "Impor manual sukses! Masuk ke permainan...", Toast.LENGTH_SHORT).show();
                    markReadyAndProceed();
                } else {
                    String msg = "Impor selesai: " + finalImported + " berkas berhasil.";
                    if (!mismatchList.isEmpty()) {
                        msg += "\\nBerkas tidak valid/diubah: " + TextUtils.join(", ", mismatchList) + ". Berkas resmi akan diunduh.";
                    }
                    Toast.makeText(this, msg, Toast.LENGTH_LONG).show();
                    checkFilesAndPrepareQueue(currentManifest, downloadDir);
                }
            });
        }, "ViceSide-ManualImport").start();
    }

    private void extractZip(File zipFile, File destDir) throws IOException {
        mainHandler.post(() -> {
            if (statusTitle != null) {
                statusTitle.setText("Mengekstrak " + zipFile.getName() + "...");
            }
            if (progressBar != null) {
                progressBar.setIndeterminate(false);
                progressBar.setProgress(0);
            }
        });

        byte[] buffer = new byte[65536];
        try (InputStream is = new FileInputStream(zipFile);
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

    private String fetchManifestJson() {
        String json = downloadStringWithTimeout(PRIMARY_MANIFEST_URL, 15000);
        if (json != null && !json.trim().isEmpty()) {
            return json;
        }
        Log.w(TAG, "Primary manifest URL failed, trying fallback URL: " + FALLBACK_MANIFEST_URL);
        return downloadStringWithTimeout(FALLBACK_MANIFEST_URL, 15000);
    }

    private String downloadStringWithTimeout(String urlString, int timeout) {
        HttpURLConnection conn = null;
        try {
            URL url = new URL(urlString);
            conn = (HttpURLConnection) url.openConnection();
            conn.setConnectTimeout(timeout);
            conn.setReadTimeout(timeout);
            conn.setInstanceFollowRedirects(true);
            conn.setRequestProperty("User-Agent", "ViceSideClient/1.0");
            int code = conn.getResponseCode();
            if (code >= 200 && code < 300) {
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream(), "UTF-8"))) {
                    StringBuilder sb = new StringBuilder();
                    String line;
                    while ((line = reader.readLine()) != null) {
                        sb.append(line).append('\\n');
                    }
                    return sb.toString();
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "Failed to download string from " + urlString, e);
        } finally {
            if (conn != null) conn.disconnect();
        }
        return null;
    }

    private ManifestData parseManifest(String jsonString) {
        try {
            JSONObject obj = new JSONObject(jsonString);
            int version = obj.getInt("version");
            String title = obj.optString("title", "Vice Side Data");
            ManifestData data = new ManifestData(version, title);
            JSONArray arr = obj.getJSONArray("files");
            for (int i = 0; i < arr.length(); i++) {
                JSONObject fObj = arr.getJSONObject(i);
                data.files.add(new ManifestFile(
                        fObj.getString("id"),
                        fObj.getString("url"),
                        fObj.getLong("size"),
                        fObj.getString("sha256"),
                        fObj.optString("extract_to", ".")
                ));
            }
            return data;
        } catch (Exception e) {
            Log.e(TAG, "Manifest parsing error", e);
            return null;
        }
    }

    private void cleanObsoleteFiles(File downloadDir, ManifestData manifest) {
        if (!downloadDir.exists() || manifest == null) return;
        Set<String> validNames = new HashSet<>();
        for (ManifestFile mf : manifest.files) {
            validNames.add(mf.fileName);
            validNames.add(mf.fileName + ".part");
            validNames.add(mf.fileName + ".part.temp");
        }
        File[] files = downloadDir.listFiles();
        if (files != null) {
            for (File f : files) {
                if (!validNames.contains(f.getName())) {
                    Log.i(TAG, "Deleting obsolete download file: " + f.getName());
                    f.delete();
                }
            }
        }
    }

    public static String calculateSha256(File file) {
        if (file == null || !file.exists() || !file.isFile()) return "";
        try (InputStream fis = new BufferedInputStream(new FileInputStream(file), 65536)) {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] buffer = new byte[65536];
            int read;
            while ((read = fis.read(buffer)) != -1) {
                digest.update(buffer, 0, read);
            }
            byte[] hash = digest.digest();
            StringBuilder sb = new StringBuilder();
            for (byte b : hash) {
                sb.append(String.format(Locale.US, "%02x", b));
            }
            return sb.toString();
        } catch (Exception e) {
            Log.e(TAG, "Error calculating SHA-256 for " + file.getAbsolutePath(), e);
            return "";
        }
    }

    public static boolean moveOrCopyFile(File source, File target) {
        if (source.renameTo(target)) {
            return true;
        }
        byte[] buffer = new byte[65536];
        try (InputStream in = new FileInputStream(source);
             FileOutputStream out = new FileOutputStream(target)) {
            int read;
            while ((read = in.read(buffer)) != -1) {
                out.write(buffer, 0, read);
            }
            out.flush();
        } catch (IOException e) {
            if (target.exists()) target.delete();
            return false;
        }
        if (target.length() == source.length()) {
            source.delete();
            return true;
        } else {
            if (target.exists()) target.delete();
            return false;
        }
    }

    private boolean copyDirectory(File source, File target) {
        if (source.isDirectory()) {
            if (!target.exists()) target.mkdirs();
            File[] children = source.listFiles();
            if (children != null) {
                for (File child : children) {
                    copyDirectory(child, new File(target, child.getName()));
                }
            }
            return true;
        } else {
            return moveOrCopyFile(source, target);
        }
    }

    private void markReadyAndProceed() {
        ConfigValidator.validateConfigFiles(this);
        mainHandler.post(this::launchMainActivity);
    }

    private void showErrorDialog(String errorMsg) {
        if (statusTitle != null) {
            statusTitle.setText("Kendala Pembaruan Data Game");
        }
        View dialogView = getLayoutInflater().inflate(R.layout.dialog_update_prompt, null, false);
        TextView titleView = dialogView.findViewById(R.id.update_prompt_title);
        TextView bodyView = dialogView.findViewById(R.id.update_prompt_body);
        TextView primaryButton = dialogView.findViewById(R.id.update_prompt_primary);
        TextView secondaryButton = dialogView.findViewById(R.id.update_prompt_secondary);

        if (titleView != null) titleView.setText("Pembaruan Data Terkendala");
        if (bodyView != null) {
            bodyView.setText((errorMsg != null ? errorMsg : "Gagal memproses berkas data game.")
                    + "\\n\\nPastikan perangkat terhubung ke internet dan memiliki ruang kosong minimal 3 GB, atau gunakan tombol 'Impor dari Folder'.");
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
                setupUi();
                startUpdateFlow();
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
    print("[*] Replaced EntryActivity.java with client-side downloader & manual importer")

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

    # Strip any bundled game-data sourceSets
    app_text = re.sub(r"\s*assets\.srcDirs\s*\+=\s*\['\.\./game-data'\]", "", app_text)

    if "signingConfigs {" not in app_text:
        insert_pos = app_text.find("buildTypes {")
        if insert_pos != -1:
            signing_block = (
                "    signingConfigs {\n"
                "        release {\n"
                "            storeFile file(System.getenv('KEYSTORE_PATH') ?: (project.findProperty('KEYSTORE_FILE') ?: (file('release.keystore').exists() ? 'release.keystore' : '../release.keystore')))\n"
                "            storePassword (System.getenv('KEYSTORE_PASSWORD') ?: (project.findProperty('KEYSTORE_PASSWORD') ?: ''))\n"
                "            keyAlias (System.getenv('KEY_ALIAS') ?: (project.findProperty('KEY_ALIAS') ?: ''))\n"
                "            keyPassword (System.getenv('KEY_PASSWORD') ?: (System.getenv('KEYSTORE_PASSWORD') ?: (project.findProperty('KEY_PASSWORD') ?: (project.findProperty('KEYSTORE_PASSWORD') ?: ''))))\n"
                "        }\n"
                "    }\n\n"
            )
            app_text = app_text[:insert_pos] + signing_block + app_text[insert_pos:]

    app_text = re.sub(
        r"//signingConfig\s+signingConfigs\.release",
        "signingConfig signingConfigs.release",
        app_text
    )
    app_gradle.write_text(app_text, encoding="utf-8")
    print("[*] Configured app/build.gradle (signingConfigs.release, dynamic versionCode, no bundled game data)")

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
    patch_gradle_properties(root)
    patch_samp_orientation(root)
    patch_splash_layout(root)
    patch_entry_activity(root)
    patch_app_gradle(root)

    print("[SUCCESS] All single-server, CEF, client-side downloader, and importer patches applied successfully.")

if __name__ == "__main__":
    main()
