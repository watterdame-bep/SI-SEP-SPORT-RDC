/**
 * Morpho MorFinEnroll — API client pour lecteur d'empreintes (capteur_fichier).
 * URI configurable via window.MORPHO_SERVICE_URI (ex: https://localhost:8032/morfinenroll/)
 * Version asynchrone (Promises) pour éviter "Synchronous XMLHttpRequest on the main thread is deprecated".
 */
var uri = (typeof window.MORPHO_SERVICE_URI !== "undefined" && window.MORPHO_SERVICE_URI) ? window.MORPHO_SERVICE_URI : "http://localhost:8032/morfinenroll/";

function getHttpError(jqXHR, thrownError) {
    var err = "Unhandled Exception";
    if (jqXHR.status === 0) {
        err = 'Service Unavailable';
    } else if (jqXHR.status == 404) {
        err = 'Requested page not found';
    } else if (jqXHR.status == 500) {
        err = 'Internal Server Error';
    } else if (thrownError === 'parsererror') {
        err = 'Requested JSON parse failed';
    } else if (thrownError === 'timeout') {
        err = 'Time out error';
    } else if (thrownError === 'abort') {
        err = 'Ajax request aborted';
    } else {
        err = 'Unhandled Error';
    }
    return err;
}

/**
 * Appel asynchrone au service Morpho — retourne une Promise (plus de blocage du thread principal).
 */
function PostMorFinEnrollClient(method, jsonData, isBodyAvailable) {
    return new Promise(function(resolve) {
        var options = {
            type: "POST",
            async: true,
            crossDomain: true,
            url: uri + method,
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            processData: false,
            timeout: 65000,
            success: function (data) {
                resolve({ httpStaus: true, data: data });
            },
            error: function (jqXHR, ajaxOptions, thrownError) {
                resolve({ httpStaus: false, err: getHttpError(jqXHR, thrownError) });
            }
        };
        if (isBodyAvailable === 1) {
            options.data = jsonData;
        }
        $.ajax(options);
    });
}

function GetMorFinEnrollInfo(fingerType, clientKey) {
    var MorFinEnrollRequest = { "FingerType": fingerType, "ClientKey": clientKey };
    return PostMorFinEnrollClient("info", JSON.stringify(MorFinEnrollRequest), 1);
}

function CaptureFinger(timeout, slap, FingerPosition, NFIQ_Quality) {
    var MorFinEnrollRequest = {
        "TimeOut": timeout,
        "Slap": slap,
        "FingerPosition": FingerPosition,
        "NFIQ_Quality": NFIQ_Quality
    };
    return PostMorFinEnrollClient("capture", JSON.stringify(MorFinEnrollRequest), 1);
}

function GetImage(imgformat, compressionRatio) {
    var MorFinEnrollRequest = { "ImgFormat": imgformat, "CompressionRatio": compressionRatio };
    return PostMorFinEnrollClient("getimage", JSON.stringify(MorFinEnrollRequest), 1);
}

function GetTemplate(tempFormat) {
    var MorFinEnrollRequest = { "TempFormat": tempFormat };
    return PostMorFinEnrollClient("gettemplate", JSON.stringify(MorFinEnrollRequest), 1);
}

function MorFinEnrollMatchTemplate(gallaryTemp, probTemp, tempFormat) {
    var MorFinEnrollRequest = { "GallaryTemp": gallaryTemp, "ProbTemp": probTemp, "TempFormat": tempFormat };
    return PostMorFinEnrollClient("matchtemplate", JSON.stringify(MorFinEnrollRequest), 1);
}

function MorFinEnrollCheckDevice() {
    return PostMorFinEnrollClient("checkdevice", "", 0);
}

function MorFinEnrollGetSupportedDevice() {
    return PostMorFinEnrollClient("getsupporteddevice", "", 0);
}

function MorFinEnrollGetConnectedDevice() {
    return PostMorFinEnrollClient("getconnecteddevice", "", 0);
}

function MorFinEnrollUnInit() {
    return PostMorFinEnrollClient("uninitdevice", "", 0);
}

function MorFinEnrollRequest(BiometricArray) {
    this.Biometrics = BiometricArray;
}
