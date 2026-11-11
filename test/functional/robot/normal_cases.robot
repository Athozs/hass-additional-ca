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
    Should Be Equal As Integers    ${certs_count}    3
    # Make the HTTPS request
    ${response} =  Wait Until Keyword Succeeds    120s    10s    Run HomeAssistant Action Rest Command    additional_ca_test
    Should Be Equal As Strings    200  ${response.json()}[service_response][status]


Make an HTTPS request with Custom CA on hon-smarthome.com
    ${response} =  Wait Until Keyword Succeeds    120s    10s    Run HomeAssistant Action Rest Command    hon_ca_test
    Should Be Equal As Strings    200  ${response.json()}[service_response][status]


Remove unused Certificates
    [Documentation]  Check that unused certificates are removed at HomeAssistant startup
    ...              and that HomeAssistant no longer trusts a server signed by a removed CA
    Copy File    test/functional/files/configuration_test_cases.yaml    test/functional/files/config/configuration.yaml
    Attempt to restart HomeAssistant
    HomeAssistant Logs Should Not Contain    Forcing load of
    HomeAssistant Logs Should Not Contain    Removing unused certificate
    Certificate Should Exist in HomeAssistant    rapidssl_ca_RapidSSLTLSRSACAG1.crt.pem
    Sleep    30    # avoid too early false positive code 200 on restart via REST API
    Copy File    test/functional/files/configuration_base.yaml    test/functional/files/config/configuration.yaml
    Attempt to restart HomeAssistant
    HomeAssistant Logs Should Contain    Removing unused certificate: rapidssl_ca_RapidSSLTLSRSACAG1.crt.pem
    Certificate Should Not Exist in HomeAssistant    rapidssl_ca_RapidSSLTLSRSACAG1.crt.pem
    Certificate Should Exist in HomeAssistant    simple_ca_simple-https-server.pem
    ${response} =  Wait Until Keyword Succeeds    120s    10s    Run HomeAssistant Action Rest Command    additional_ca_test
    Should Be Equal As Strings    200  ${response.json()}[service_response][status]
    # hon and rapidssl servers are also trusted by system CAs, so remove the private mkcert CA to check trust is revoked
    Copy File    test/functional/files/configuration_without_simple_ca.yaml    test/functional/files/config/configuration.yaml
    Attempt to restart HomeAssistant
    HomeAssistant Logs Should Contain    Removing unused certificate: simple_ca_simple-https-server.pem
    Certificate Should Not Exist in HomeAssistant    simple_ca_simple-https-server.pem
    # SSL context is loaded before the integration removes the CA, so a second restart is needed
    Sleep    30    # avoid too early false positive code 200 on restart via REST API
    Attempt to restart HomeAssistant
    Wait Until Keyword Succeeds    120s    10s
    ...    Run Keyword And Expect Error    HTTPError: 500 Server Error: *
    ...    Run HomeAssistant Action Rest Command    additional_ca_test
    HomeAssistant Logs Should Match Regex    Cannot connect to host simple-https-server:4433 ssl:True .SSLCertVerificationError: ..*, '.SSL: CERTIFICATE_VERIFY_FAILED. certificate verify failed: unable to get local issuer certificate ..*.'..
