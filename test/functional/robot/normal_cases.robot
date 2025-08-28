*** Settings ***
Documentation     A test suite for normal cases.

Resource  integration.resource

Suite Setup  Normal Suite Setup
Suite Teardown  Custom Suite Teardown


*** Test Cases ***

Make an HTTPS request with System CA
    ${response} =  Wait Until Keyword Succeeds    120s    10s    Run HomeAssistant Action Rest Command    https_google_test
    Should Be Equal As Strings    200  ${response.json()}[service_response][status]


Make an HTTPS request with Custom CA on self-signed.badssl.com
    # [Setup]  Attempt to restart HomeAssistant
    ${response} =  Wait Until Keyword Succeeds    120s    10s    Run HomeAssistant Action Rest Command    additional_ca_test
    Should Be Equal As Strings    200  ${response.json()}[service_response][status]
    HomeAssistant Logs Should Not Contain    Forcing load of


Make an HTTPS request with Custom CA on hon-smarthome.com
    ${response} =  Wait Until Keyword Succeeds    120s    10s    Run HomeAssistant Action Rest Command    hon_ca_test
    Should Be Equal As Strings    200  ${response.json()}[service_response][status]


Forcing Load of Certificates
    [Setup]  Copy File    test/integration/files/configuration_force_additional_ca.yaml    test/integration/files/config/configuration.yaml
    Attempt to restart HomeAssistant
    HomeAssistant Logs Should Contain    Forcing load of
