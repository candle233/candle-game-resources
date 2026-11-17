using System.Collections;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;
namespace WorkflowHarness.Tests
{
    public sealed class PlayModeConnectivityTests
    {
        [UnityTest, Category("HarnessConnectivity")]
        public IEnumerator GameObjectLifecycleWorks()
        {
            var obj = new GameObject("HarnessConnectivity");
            Assert.IsTrue(obj.activeSelf);
            Object.Destroy(obj);
            yield return null;
            Assert.IsTrue(obj == null);
        }
    }
}
