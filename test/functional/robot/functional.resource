*** Settings ***
Documentation     Resource file for functional tests

Library    Process
Library    RequestsLibrary
Library    OperatingSystem


*** Variables ***
${GITHUB_WORKSPACE} =  to_be_overridden
${HASS_TOKEN} =  to_be_overridden


*** Keywords ***

Normal Suite Setup
    OperatingSystem.Copy File    test/functional/files/configuration_no_force.yaml    test/functional/files/config/configuration.yaml
    Start HomeAssistant container
    # HomeAssistant needs to be restarted to take new CAs into account
    Attempt to restart HomeAssistant


Error Suite Setup
    OperatingSystem.Copy File    test/functional/files/configuration_base.yaml    test/functional/files/config/configuration.yaml
    Start HomeAssistant container


Custom Suite Teardown
    Stop HomeAssistant container


Start HomeAssistant container
    [Arguments]    ${environment_var}=foo=bar
    @{docker_run_args} =  Create List
    ...  run
    ...  --rm
    ...  --name  homeassistant
    ...  --env  TZ=UTC
    ...  --env  PYTHONUNBUFFERED=1
    ...  --env  ${environment_var}
    ...  -v  ${GITHUB_WORKSPACE}/test/functional/files/config:/config
    ...  --network  robot
    ...  -p  8123:8123
    ...  -d
    ...  ghcr.io/home-assistant/home-assistant:stable
    ${result} =    Process.Run Process    docker  @{docker_run_args}  stdout=stdout_docker_run2.txt  stderr=STDOUT
    Should Be Equal As Integers    ${result.rc}    0
    Log To Console  container homeassistant ${result.stdout} created
    Wait Until Keyword Succeeds    120s    5s    Wait Until Additional CA integration is loaded
    RETURN    ${result.stdout}


Stop HomeAssistant container
    @{docker_stop_args} =  Create List  stop  homeassistant
    ${result} =    Process.Run Process    docker  @{docker_stop_args}  stdout=stdout_docker_stop.txt  stderr=STDOUT
    Should Be Equal As Integers    ${result.rc}    0
    Wait Until Keyword Succeeds    30s    2s    Container Should Not Exist    homeassistant
    Log To Console  container ${result.stdout} stopped
    RETURN    ${result.stdout}


Wait Until Additional CA integration is loaded
    Wait Until Keyword Succeeds    120s    5s    Additional CA integration is loaded


Additional CA integration is loaded
    [Documentation]    This keyword returns True or False if Additional CA integration is loaded or not
    ${headers}  Create Dictionary
    ...    Authorization=Bearer ${HASS_TOKEN}
    ...    Content-Type=application/json
    ${response} =  RequestsLibrary.GET  http://localhost:8123/api/config/config_entries/entry
    ...    headers=${headers}

    # Check if additional_ca domain is loaded
    ${additional_ca_found} =  Set Variable  ${False}
    FOR  ${entry}  IN  @{response.json()}
        IF  '${entry["domain"]}' == 'additional_ca' and '${entry["state"]}' == 'loaded'
            ${additional_ca_found} =  Set Variable  ${True}
            Log To Console  Additional CA integration found and loaded
            BREAK
        END
    END
    Should Be True  ${additional_ca_found}  msg=Additional CA integration not found or not loaded


Run HomeAssistant Action Rest Command
    [Arguments]    ${command_name}
    ${headers}  Create Dictionary
    ...    Authorization=Bearer ${HASS_TOKEN}
    ...    Content-Type=application/json
    ${response} =    RequestsLibrary.POST  http://localhost:8123/api/services/rest_command/${command_name}
    ...  params=return_response
    ...  headers=${headers}
    RETURN  ${response}


Attempt to restart HomeAssistant
    [Documentation]    Restart HomeAssistant from API and wait for Additional CA integration to be loaded
    ${headers}  Create Dictionary
    ...    Authorization=Bearer ${HASS_TOKEN}
    ...    Content-Type=application/json
    ${response} =    Wait Until Keyword Succeeds    120s    5s    RequestsLibrary.POST  http://localhost:8123/api/services/homeassistant/restart
    ...  headers=${headers}
    Wait Until Additional CA integration is loaded
    RETURN  ${response}


Container Should Not Exist
    [Arguments]    ${container_name}
    @{docker_run_args} =  Create List
    ...    ps
    ...    -a
    ...    --filter    name=${container_name}
    ...    --format    {{.Names}}
    ${result} =    Process.Run Process    docker    @{docker_run_args}    stdout=stdout_docker_ps.txt    stderr=STDOUT
    Should Be Equal As Integers    ${result.rc}    0
    Should Not Contain    ${result.stdout}    ${container_name}


HomeAssistant Logs Should Not Contain
    [Arguments]    ${string_to_check}
    ${log_content} =    OperatingSystem.Get File    test/functional/files/config/home-assistant.log
    Should Not Contain    ${log_content}    ${string_to_check}    msg=HomeAssistant logs contain the unexpected string: '${string_to_check}'    values=False


HomeAssistant Logs Should Contain
    [Arguments]    ${string_to_check}
    ${log_content} =    OperatingSystem.Get File    test/functional/files/config/home-assistant.log
    Should Contain    ${log_content}    ${string_to_check}    msg=HomeAssistant logs do not contain the expected string: '${string_to_check}'    values=False


HomeAssistant Logs Should Match Regex
    [Arguments]    ${regex}
    ${log_content} =    OperatingSystem.Get File    test/functional/files/config/home-assistant.log
    Should Match Regexp    ${log_content}    ${regex}    msg=HomeAssistant logs do not contain the expected regex: '${regex}'    values=False
