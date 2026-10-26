/**
 * Robust clipboard utility that works across secure contexts (HTTPS/localhost)
 * and non-secure local LAN HTTP contexts (e.g. http://192.168.X.X:8000).
 */
export async function copyToClipboard(text) {
  if (!text) return false;

  // Try modern navigator.clipboard API if available and secure
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (err) {
      console.warn("navigator.clipboard failed, attempting fallback:", err);
    }
  }

  // Fallback for non-secure HTTP contexts (e.g. http://192.168.1.X:8000)
  try {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.top = "-9999px";
    textArea.style.left = "-9999px";
    textArea.style.opacity = "0";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    const successful = document.execCommand("copy");
    document.body.removeChild(textArea);
    return Boolean(successful);
  } catch (err) {
    console.error("Fallback clipboard copy failed:", err);
    return false;
  }
}
