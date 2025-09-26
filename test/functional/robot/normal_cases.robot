*** Settings ***
Documentation     A test suite for normal cases.

Resource  functional.resource

Suite Setup  Normal Suite Setup
Suite Teardown  Custom Suite Teardown


*** Test Cases ***

Make an HTTPS request with System CA
    ${response} =  Wait Until Keyword Succeeds    120s    10s    Run HomeAssistant Action Rest Command    https_google_test
    Should Be Equal As Strings    200  ${response.json()}[service_response][status]


Make an HTTPS request with Custom CA on simple-https-server
    ${response} =  Wait Until Keyword Succeeds    120s    10s    Run HomeAssistant Action Rest Command    additional_ca_test
    Should Be Equal As Strings    200  ${response.json()}[service_response][status]
    HomeAssistant Logs Should Not Contain    Forcing load of


Make an HTTPS request with Custom CA on hon-smarthome.com
    ${response} =  Wait Until Keyword Succeeds    120s    10s    Run HomeAssistant Action Rest Command    hon_ca_test
    Should Be Equal As Strings    200  ${response.json()}[service_response][status]


Forcing Load of Certificates
    [Setup]  Copy File    test/functional/files/configuration_force_additional_ca.yaml    test/functional/files/config/configuration.yaml
    Attempt to restart HomeAssistant
    HomeAssistant Logs Should Contain    Forcing load of
    ${response} =  Wait Until Keyword Succeeds    120s    10s    Run HomeAssistant Action Rest Command    additional_ca_test
    Should Be Equal As Strings    200  ${response.json()}[service_response][status]
