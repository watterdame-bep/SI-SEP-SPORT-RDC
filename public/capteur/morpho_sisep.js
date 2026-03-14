/**
 * SI-SEP — Wrapper Morpho pour prélèvement 4-4-2 (main droite, main gauche, 2 pouces).
 * Utilise morfinenroll.js (service local http(s)://localhost:8032/morfinenroll/).
 * stepIndex: 0 = main droite (4 doigts), 1 = main gauche (4 doigts), 2 = 2 pouces.
 * API asynchrone (retourne des Promises).
 */
var MorphoSISEP = (function() {
    var SLAP_MAP = [1, 0, 2]; // step 0 → slap 1 (right), step 1 → slap 0 (left), step 2 → slap 2 (thumbs)
    var TIMEOUT = 50;
    var NFIQ_QUALITY = 30;
    var TEMPLATE_FORMAT = "0"; // FMR_V2005
    var deviceInitialized = false;
    var fingerPosition = {
        LEFT_LITTLE: false, LEFT_RING: false, LEFT_MIDDLE: false, LEFT_INDEX: false,
        RIGHT_INDEX: false, RIGHT_MIDDLE: false, RIGHT_RING: false, RIGHT_LITTLE: false,
        LEFT_THUMB: false, RIGHT_THUMB: false
    };

    function ensureDeviceInit() {
        if (deviceInitialized) return Promise.resolve({ ok: true });
        if (typeof GetMorFinEnrollInfo !== "function") return Promise.resolve({ ok: true });
        return GetMorFinEnrollInfo("0", "").then(function(res) {
            if (res.httpStaus && res.data && res.data.ErrorCode === "0") {
                deviceInitialized = true;
                return { ok: true };
            }
            return { ok: false, error: res.data && res.data.ErrorDescription ? res.data.ErrorDescription : "Initialisation du lecteur échouée" };
        });
    }

    /**
     * Effectue la capture pour une étape (0, 1 ou 2). Retourne une Promise<{success, imageBase64?, templateBase64?, capturedFingers?, error?}>.
     */
    function captureStep(stepIndex) {
        if (stepIndex < 0 || stepIndex > 2) {
            return Promise.resolve({ success: false, error: "Step invalide" });
        }
        if (typeof CaptureFinger !== "function" || typeof GetTemplate !== "function") {
            return Promise.resolve({ success: false, error: "API Morpho non chargée (morfinenroll.js). Vérifiez que jQuery et morfinenroll.js sont chargés." });
        }
        var slap = SLAP_MAP[stepIndex];
        return ensureDeviceInit().then(function(initResult) {
            if (!initResult.ok) {
                return { success: false, error: initResult.error || "Lecteur non initialisé" };
            }
            return CaptureFinger(TIMEOUT, slap, fingerPosition, NFIQ_QUALITY);
        }).then(function(resCapture) {
            if (!resCapture.httpStaus) {
                return { success: false, error: resCapture.err || "Service indisponible" };
            }
            if (!resCapture.data || resCapture.data.ErrorCode !== "0") {
                return {
                    success: false,
                    error: (resCapture.data && resCapture.data.ErrorDescription) ? resCapture.data.ErrorDescription : "Capture échouée"
                };
            }
            var imageBase64 = null;
            var capturedFingers = []; // Images par doigt (pour pouces: [gauche, droit])
            if (resCapture.data.CaptureData && resCapture.data.CaptureData.SlapBoxedBmpImage) {
                imageBase64 = resCapture.data.CaptureData.SlapBoxedBmpImage;
            }
            if (resCapture.data.CaptureData && resCapture.data.CaptureData.CapturedFingers && resCapture.data.CaptureData.CapturedFingers.length) {
                for (var f = 0; f < resCapture.data.CaptureData.CapturedFingers.length; f++) {
                    if (resCapture.data.CaptureData.CapturedFingers[f].FingerBitmapStr) {
                        capturedFingers.push(resCapture.data.CaptureData.CapturedFingers[f].FingerBitmapStr);
                    }
                }
            }
            return GetTemplate(TEMPLATE_FORMAT).then(function(resTemplate) {
                var templateBase64 = null;
                if (resTemplate.httpStaus && resTemplate.data && resTemplate.data.ErrorCode === "0" && resTemplate.data.Fingers && resTemplate.data.Fingers.fingerbase64) {
                    var arr = resTemplate.data.Fingers.fingerbase64;
                    for (var i = 0; i < arr.length; i++) {
                        if (arr[i]) {
                            templateBase64 = arr[i];
                            break;
                        }
                    }
                }
                return {
                    success: true,
                    imageBase64: imageBase64,
                    templateBase64: templateBase64 || null,
                    capturedFingers: capturedFingers
                };
            });
        });
    }

    function checkDevice() {
        if (typeof MorFinEnrollCheckDevice !== "function") {
            return Promise.resolve({ available: false, error: "API non chargée" });
        }
        return MorFinEnrollCheckDevice().then(function(res) {
            if (!res.httpStaus) return { available: false, error: res.err };
            if (res.data && res.data.ErrorCode === "0") return { available: true };
            return { available: false, error: (res.data && res.data.ErrorDescription) ? res.data.ErrorDescription : "Appareil non prêt" };
        });
    }

    return {
        captureStep: captureStep,
        checkDevice: checkDevice
    };
})();
