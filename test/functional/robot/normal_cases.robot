*** Settings ***
Documentation     A test suite for normal cases.

Resource  functional.resource

Suite Setup  Normal Suite Setup
Suite Teardown  Custom Suite Teardown

Test Teardown    Custom Test Teardown    ${TEST NAME}


*** Test Cases ***

Make an HTTPS request with System CA
    ${response} =  Wait Until Keyword Succeeds    120s    10s    Run HomeAssistant Action Rest Command    https_google_test
    Should Be Equal As Strings    200  ${response.json()}[service_response][status]


Make an HTTPS request with Custom CA on simple-https-server
    # certificate change time should not be the same after the restart of HomeAssistant because Additional CA integration copies certs on each startup
    ${cert_ctime_1} =  Get Change Time of Certificate    simple_ca_simple-https-server.pem
    Sleep  2
    Attempt to restart HomeAssistant
    HomeAssistant Logs Should Not Contain    Forcing load of
    ${cert_ctime_2} =  Get Change Time of Certificate    simple_ca_simple-https-server.pem
    Should Be True    ${cert_ctime_2} > ${cert_ctime_1}
    ${certs_count} =  Count CA in HomeAssistant
    Should Be Equal As Integers    ${certs_count}    4
    # Make the HTTPS request
    ${response} =  Wait Until Keyword Succeeds    120s    10s    Run HomeAssistant Action Rest Command    additional_ca_test
    Should Be Equal As Strings    200  ${response.json()}[service_response][status]


Make an HTTPS request with Custom CA on hon-smarthome.com
    ${response} =  Wait Until Keyword Succeeds    120s    10s    Run HomeAssistant Action Rest Command    hon_ca_test
    Should Be Equal As Strings    200  ${response.json()}[service_response][status]


Remove unused Certificates
    [Documentation]  Check that unused certificates are removed at HomeAssistant startup
    Copy File    test/functional/files/configuration_test_cases.yaml    test/functional/files/config/configuration.yaml
    Attempt to restart HomeAssistant
    HomeAssistant Logs Should Not Contain    Forcing load of
    HomeAssistant Logs Should Not Contain    Removing unused certificate
    Certificate Should Exist in HomeAssistant    hon_ca_hon_cert.crt
    Certificate Should Exist in HomeAssistant    rapidssl_ca_RapidSSLTLSRSACAG1.crt.pem
    Copy File    test/functional/files/configuration_base.yaml    test/functional/files/config/configuration.yaml
    Attempt to restart HomeAssistant
    HomeAssistant Logs Should Contain    Removing unused certificate: hon_ca_hon_cert.crt
    HomeAssistant Logs Should Contain    Removing unused certificate: rapidssl_ca_RapidSSLTLSRSACAG1.crt.pem
    Certificate Should Not Exist in HomeAssistant    hon_ca_hon_cert.crt
    Certificate Should Not Exist in HomeAssistant    rapidssl_ca_RapidSSLTLSRSACAG1.crt.pem
    Certificate Should Exist in HomeAssistant    simple_ca_simple-https-server.pem
    ${response} =  Wait Until Keyword Succeeds    120s    10s    Run HomeAssistant Action Rest Command    additional_ca_test
    Should Be Equal As Strings    200  ${response.json()}[service_response][status]
