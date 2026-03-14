var uri = "https://localhost:8032/morfinenroll/"; //Secure
// var uri = "http://localhost:8032/morfinenroll/"; //Non-Secure
//var uri = "http://rd.mxface.ai:8032/morfinenroll/"; //Non-Secure

//If you want to browse this url , then please remove '/' from the end of uri

function GetMorFinEnrollInfo(fingerType , clientKey) {
    var MorFinEnrollRequest = {
        "FingerType": fingerType,
        "ClientKey": clientKey
    };
    var jsondata = JSON.stringify(MorFinEnrollRequest);
    return PostMorFinEnrollClient("info", jsondata, 1);
}

function CaptureFinger(timeout, slap, FingerPosition ,NFIQ_Quality) {
    var MorFinEnrollRequest = {
        "TimeOut": timeout,
        "Slap": slap,
        "FingerPosition": FingerPosition,
        "NFIQ_Quality": NFIQ_Quality
    };
    var jsondata = JSON.stringify(MorFinEnrollRequest);
    return PostMorFinEnrollClient("capture", jsondata, 1);
}

function GetImage(imgformat, compressionRatio) {
    var MorFinEnrollRequest = {
        "ImgFormat": imgformat,
        "CompressionRatio": compressionRatio
    };
    var jsondata = JSON.stringify(MorFinEnrollRequest);
    return PostMorFinEnrollClient("getimage", jsondata, 1);
}

function GetTemplate(tempFormat) {
    var MorFinEnrollRequest = {
        "TempFormat": tempFormat
    };
    var jsondata = JSON.stringify(MorFinEnrollRequest);
    return PostMorFinEnrollClient("gettemplate", jsondata, 1);
}

function MorFinEnrollMatchTemplate(gallaryTemp, probTemp, tempFormat) {
    var MorFinEnrollRequest = {
        "GallaryTemp": gallaryTemp,
        "ProbTemp": probTemp,
        "TempFormat": tempFormat
    };
    var jsondata = JSON.stringify(MorFinEnrollRequest);
    return PostMorFinEnrollClient("matchtemplate", jsondata, 1);
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

function PostMorFinEnrollClient(method, jsonData, isBodyAvailable) {

    var res;
    if (isBodyAvailable == 0) {
        $.support.cors = true;
        var httpStaus = false;
        $.ajax({
            type: "POST",
            async: false,
            crossDomain: true,
            url: uri + method,
            contentType: "application/json; charset=utf-8",
            //data: jsonData,
            dataType: "json",
            processData: false,
            success: function (data) {
                httpStaus = true;
                res = { httpStaus: httpStaus, data: data };
            },
            error: function (jqXHR, ajaxOptions, thrownError) {
                res = { httpStaus: httpStaus, err: getHttpError(jqXHR) };
            },
        });
    }
    else {
        $.support.cors = true; 
        var httpStaus = false;
        $.ajax({
            type: "POST",
            async: false,
            crossDomain: true,
            url: uri + method,
            contentType: "application/json; charset=utf-8",
            data: jsonData,
            dataType: "json",
            processData: false,
            success: function (data) {
                httpStaus = true;
                res = { httpStaus: httpStaus, data: data };
            },
            error: function (jqXHR, ajaxOptions, thrownError) {
                res = { httpStaus: httpStaus, err: getHttpError(jqXHR) };
            },
        });
    }
    return res;
}

function getHttpError(jqXHR) {
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

function MorFinEnrollRequest(BiometricArray) {
    this.Biometrics = BiometricArray;
}