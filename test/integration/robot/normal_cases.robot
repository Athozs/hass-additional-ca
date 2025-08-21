*** Settings ***
Documentation     A test suite for normal cases.

Library   RequestsLibrary
Resource  integration.resource

Suite Setup  Normal Suite Setup
Suite Teardown  Custom Suite Teardown


*** Test Cases ***

Make an HTTPS request with System CA
    ${response} =  Wait Until Keyword Succeeds    120s    10s    Run HomeAssistant Action Rest Command    https_google_test
    Should Be Equal As Strings    200  ${response.json()}[service_response][status]


Make an HTTPS request with Custom CA on self-signed.badssl.com
    ${response} =  Wait Until Keyword Succeeds    120s    10s    Run HomeAssistant Action Rest Command    additional_ca_test
    Should Be Equal As Strings    200  ${response.json()}[service_response][status]


Make an HTTPS request with Custom CA on hon-smarthome.com
    ${response} =  Wait Until Keyword Succeeds    120s    10s    Run HomeAssistant Action Rest Command    hon_ca_test
    Should Be Equal As Strings    200  ${response.json()}[service_response][status]
