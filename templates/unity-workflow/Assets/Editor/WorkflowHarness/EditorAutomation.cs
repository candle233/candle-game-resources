using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace WorkflowHarness
{
    public static class EditorAutomation
    {
        [Serializable]
        private sealed class Receipt
        {
            public string status = "PASS";
            public string unityVersion = Application.unityVersion;
            public string target = "";
            public string output = "";
        }
        private static string Argument(string key)
        {
            var args = Environment.GetCommandLineArgs();
            var i = Array.IndexOf(args, key);
            if (i < 0 || i + 1 >= args.Length) throw new ArgumentException("Missing " + key);
            return args[i + 1];
        }
        private static void Write(Receipt receipt)
        {
            var path = Path.GetFullPath(Argument("-harnessReceipt"));
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            File.WriteAllText(path, JsonUtility.ToJson(receipt, true));
        }
        public static void Compile()
        {
            // This entry point is reached only after Unity compiles Editor scripts.
            if (EditorApplication.isCompiling) throw new InvalidOperationException("Compilation is still active");
            Write(new Receipt());
        }
        public static void Build()
        {
            var scenes = EditorBuildSettings.scenes.Where(s => s.enabled).Select(s => s.path).ToArray();
            if (scenes.Length == 0) throw new InvalidOperationException("No enabled build scenes");
            var root = Path.GetFullPath(Argument("-harnessBuildRoot"));
            var target = EditorUserBuildSettings.activeBuildTarget;
            string output;
            switch (target)
            {
                case BuildTarget.StandaloneWindows64: output = Path.Combine(root, "Game.exe"); break;
                case BuildTarget.StandaloneLinux64: output = Path.Combine(root, "Game.x86_64"); break;
                case BuildTarget.StandaloneOSX: output = Path.Combine(root, "Game.app"); break;
                case BuildTarget.WebGL: output = Path.Combine(root, "WebGL"); break;
                default: throw new NotSupportedException("Unsupported build target: " + target);
            }
            Directory.CreateDirectory(root);
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = scenes, target = target, locationPathName = output,
                options = BuildOptions.StrictMode
            });
            if (report.summary.result != BuildResult.Succeeded)
                throw new InvalidOperationException("Build failed: " + report.summary.result);
            Write(new Receipt { target = target.ToString(), output = output });
        }
    }
}
