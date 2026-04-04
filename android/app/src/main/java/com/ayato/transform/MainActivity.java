package com.ayato.transform;

import android.os.Bundle;
import androidx.appcompat.app.AppCompatActivity;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

public class MainActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // 1. Initialize Python
        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(this));
        }

        // 2. Start Flet UI Backend (Python)
        Python py = Python.getInstance();
        PyObject mainModule = py.getModule("main");
        // Start the Flet server in a separate thread if needed,
        // or just trigger the logic that provides the URL.
        mainModule.callAttr("start_app_for_android");

        // 3. Load UI in WebView (Flet Web Mode)
        WebView webView = new WebView(this);
        setContentView(webView);
        webView.setWebViewClient(new WebViewClient());
        webView.getSettings().setJavaScriptEnabled(true);
        webView.loadUrl("http://localhost:8551"); // URL from Flet
    }
}
