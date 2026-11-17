using NUnit.Framework;
using UnityEngine;
namespace WorkflowHarness.Tests
{
    public sealed class EditModeConnectivityTests
    {
        [Test, Category("HarnessConnectivity")]
        public void VectorArithmeticWorks() { Assert.AreEqual(2f, (Vector3.one + Vector3.one).x); }
    }
}
