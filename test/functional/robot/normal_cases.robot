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
    # checking that certificate is not overridden because force_additional_ca is false,
    # so certificate change time should be the same after the restart of HomeAssistant
    ${cert_ctime_1} =  Get Change Time of Certificate    simple_ca_simple-https-server.pem
    Attempt to restart HomeAssistant
    HomeAssistant Logs Should Not Contain    Forcing load of
    ${cert_ctime_2} =  Get Change Time of Certificate    simple_ca_simple-https-server.pem
    Should Be Equal As Strings    ${cert_ctime_1}    ${cert_ctime_2}
    # Make the HTTPS request
    ${response} =  Wait Until Keyword Succeeds    120s    10s    Run HomeAssistant Action Rest Command    additional_ca_test
    Should Be Equal As Strings    200  ${response.json()}[service_response][status]


Make an HTTPS request with Custom CA on hon-smarthome.com
    ${response} =  Wait Until Keyword Succeeds    120s    10s    Run HomeAssistant Action Rest Command    hon_ca_test
    Should Be Equal As Strings    200  ${response.json()}[service_response][status]


Forcing Load of Certificates
    Copy File    test/functional/files/configuration_force_additional_ca.yaml    test/functional/files/config/configuration.yaml
    ${cert_ctime_1} =  Get Change Time of Certificate    simple_ca_simple-https-server.pem
    Attempt to restart HomeAssistant
    HomeAssistant Logs Should Contain    Forcing load of
    ${cert_ctime_2} =  Get Change Time of Certificate    simple_ca_simple-https-server.pem
    Should Not Be Equal As Strings    ${cert_ctime_1}    ${cert_ctime_2}
    ${response} =  Wait Until Keyword Succeeds    120s    10s    Run HomeAssistant Action Rest Command    additional_ca_test
    Should Be Equal As Strings    200  ${response.json()}[service_response][status]


Remove unused Certificates
    Copy File    test/functional/files/configuration_no_force.yaml    test/functional/files/config/configuration.yaml
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
