*** Settings ***
Documentation     Resource file for functional tests

Library    Process
Library    RequestsLibrary
Library    OperatingSystem
Library    DateTime
Library    String


*** Variables ***
${GITHUB_WORKSPACE} =  to_be_overridden
${HASS_TOKEN} =  to_be_overridden


*** Keywords ***

Normal Suite Setup
    OperatingSystem.Copy File    test/functional/files/configuration_test_cases.yaml    test/functional/files/config/configuration.yaml
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
    ${timestamp} =    DateTime.Get Current Date    result_format=%Y%m%d-%H%M%S-%f
    ${result} =    Process.Run Process    docker  @{docker_run_args}  stdout=stdout_docker_run_${timestamp}.txt  stderr=STDOUT
    Should Be Equal As Integers    ${result.rc}    0
    Log To Console  container homeassistant ${result.stdout} created
    Wait Until Keyword Succeeds    120s    5s    Additional CA integration is loaded
    Log HomeAssistant Version to console
    RETURN    ${result.stdout}


Stop HomeAssistant container
    @{docker_stop_args} =  Create List  stop  homeassistant
    ${timestamp} =    DateTime.Get Current Date    result_format=%Y%m%d-%H%M%S-%f
    ${result} =    Process.Run Process    docker  @{docker_stop_args}  stdout=stdout_docker_stop_${timestamp}.txt  stderr=STDOUT
    Should Be Equal As Integers    ${result.rc}    0
    Wait Until Keyword Succeeds    30s    3s    Container Should Not Exist    homeassistant
    Log To Console  container ${result.stdout} stopped
    RETURN    ${result.stdout}


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
    [Documentation]    Clean home-assistant.log file, then restart HomeAssistant from API and wait for Additional CA integration to be loaded
    Clean HomeAssistant Logs File
    ${headers}  Create Dictionary
    ...    Authorization=Bearer ${HASS_TOKEN}
    ...    Content-Type=application/json
    ${response} =    Wait Until Keyword Succeeds    120s    5s    RequestsLibrary.POST  http://localhost:8123/api/services/homeassistant/restart
    ...  headers=${headers}
    Wait Until Keyword Succeeds    120s    5s    Additional CA integration is loaded
    Wait Until Keyword Succeeds    60s     5s    File Should Exist    test/functional/files/config/home-assistant.log
    Wait Until Keyword Succeeds    60s     5s    HomeAssistant Logs Should Contain    Setup of domain additional_ca took
    RETURN  ${response}


Container Should Not Exist
    [Arguments]    ${container_name}
    @{docker_run_args} =  Create List
    ...    ps
    ...    -a
    ...    --filter    name=${container_name}
    ...    --format    {{.Names}}
    ${timestamp} =    DateTime.Get Current Date    result_format=%Y%m%d-%H%M%S-%f
    ${result} =    Process.Run Process    docker    @{docker_run_args}    stdout=stdout_docker_ps_${timestamp}.txt    stderr=STDOUT
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


Certificate Should Exist in HomeAssistant
    [Arguments]    ${filename}
    @{docker_exec_args} =  Create List
    ...    exec
    ...    homeassistant
    ...    ls
    ...    /usr/local/share/ca-certificates
    ${timestamp} =    DateTime.Get Current Date    result_format=%Y%m%d-%H%M%S-%f
    ${result} =    Process.Run Process    docker    @{docker_exec_args}    stdout=stdout_docker_exec_${timestamp}.txt    stderr=STDOUT
    Should Be Equal As Integers    ${result.rc}    0
    Should Contain    ${result.stdout}    ${filename}


Certificate Should Not Exist in HomeAssistant
    [Arguments]    ${filename}
    @{docker_exec_args} =  Create List
    ...    exec
    ...    homeassistant
    ...    ls
    ...    /usr/local/share/ca-certificates
    ${timestamp} =    DateTime.Get Current Date    result_format=%Y%m%d-%H%M%S-%f
    ${result} =    Process.Run Process    docker    @{docker_exec_args}    stdout=stdout_docker_exec_${timestamp}.txt    stderr=STDOUT
    Should Be Equal As Integers    ${result.rc}    0
    Should Not Contain    ${result.stdout}    ${filename}


Get Change Time of Certificate
    [Arguments]    ${filename}
    @{docker_exec_args} =  Create List
    ...    exec
    ...    homeassistant
    ...    stat
    ...    -c
    ...    "%Z"
    ...    /usr/local/share/ca-certificates/${filename}
    ${timestamp} =    DateTime.Get Current Date    result_format=%Y%m%d-%H%M%S-%f
    ${result} =    Process.Run Process    docker    @{docker_exec_args}    stdout=stdout_docker_exec_${timestamp}.txt    stderr=STDOUT
    Should Be Equal As Integers    ${result.rc}    0
    RETURN  ${result.stdout}


Clean HomeAssistant Logs File
    @{docker_exec_args} =  Create List
    ...    exec
    ...    homeassistant
    ...    rm
    ...    /config/home-assistant.log
    ${timestamp} =    DateTime.Get Current Date    result_format=%Y%m%d-%H%M%S-%f
    ${result} =    Process.Run Process    docker    @{docker_exec_args}    stdout=stdout_docker_exec_${timestamp}.txt    stderr=STDOUT
    # no need to check result returned code == 0
    OperatingSystem.Create File    test/functional/files/config/home-assistant.log


List CAs in HomeAssistant
    @{docker_exec_args} =  Create List
    ...    exec
    ...    homeassistant
    ...    ls  -A1  /usr/local/share/ca-certificates/
    ${timestamp} =    DateTime.Get Current Date    result_format=%Y%m%d-%H%M%S-%f
    ${result} =    Process.Run Process    docker    @{docker_exec_args}    stdout=stdout_docker_exec_${timestamp}.txt    stderr=STDOUT
    Should Be Equal As Integers    ${result.rc}    0
    RETURN  ${result.stdout}


Count CA in HomeAssistant
    ${certs_list} =  List CAs in HomeAssistant
    Log    CA list in /usr/local/share/ca-certificates/:\n${certs_list}
    @{docker_exec_args} =  Create List
    ...    exec
    ...    homeassistant
    ...    find  /usr/local/share/ca-certificates/
    ...    -maxdepth  1
    ...    -type  f
    ${timestamp} =    DateTime.Get Current Date    result_format=%Y%m%d-%H%M%S-%f
    ${result} =    Process.Run Process    docker    @{docker_exec_args}    stdout=stdout_docker_exec_${timestamp}.txt    stderr=STDOUT
    Should Be Equal As Integers    ${result.rc}    0
    ${lines} =    String.Split String    ${result.stdout}    \n
    ${count} =    Get Length    ${lines}
    RETURN  ${count}

Log HomeAssistant Version to console
    @{docker_exec_args} =  Create List
    ...    exec
    ...    homeassistant
    ...    cat  /config/.HA_VERSION
    ${timestamp} =    DateTime.Get Current Date    result_format=%Y%m%d-%H%M%S-%f
    ${result} =    Process.Run Process    docker    @{docker_exec_args}    stdout=stdout_docker_exec_${timestamp}.txt    stderr=STDOUT
    Should Be Equal As Integers    ${result.rc}    0
    Log To Console    Home-Assistant Version: ${result.stdout}
    RETURN  ${result.stdout}
