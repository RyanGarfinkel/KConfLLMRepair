from src.models.response import AgentResponse

# Missing CONFIG_ prefix: Success
def test_prefix_added():
	response = AgentResponse(define=['NET'], undefine=[], reasoning='test')
	assert response.define == ['CONFIG_NET']

# Lowercase option name: Success
def test_not_uppercased():
	response = AgentResponse(define=['CONFIG_net'], undefine=[], reasoning='test')
	assert response.define == ['CONFIG_NET']

# Option with =y value suffix: Success
def test_option_with_value():
	response = AgentResponse(define=['CONFIG_X=y'], undefine=[], reasoning='test')
	assert response.define == ['CONFIG_X']

# Empty and whitespace-only strings dropped: Success
def test_empty_strings_dropped():
	response = AgentResponse(define=['', '  ', 'NET'], undefine=[], reasoning='test')
	assert response.define == ['CONFIG_NET']

# Non-ASCII characters stripped: Success
def test_non_ascii_stripped():
	response = AgentResponse(define=['CONFIG_NET官'], undefine=['CONFIG_OLD官'], reasoning='test')
	assert response.define == ['CONFIG_NET']
	assert response.undefine == ['CONFIG_OLD']

# Non-ASCII with trailing comma (tokenizer artifact): Success
def test_non_ascii_with_trailing_comma():
	response = AgentResponse(define=[], undefine=['CONFIG_DEBUG_MUTEXES官,'], reasoning='test')
	assert response.undefine == ['CONFIG_DEBUG_MUTEXES']

# Garbage string in undefine with no options before Define keyword: Success
def test_garbage_define_keyword_no_prior_options():
	garbage = "]} Optics were missing from Attempt 18's Define list: CONFIG_EXT4_FS_QUOTA, CONFIG_QUOTACTL"
	response = AgentResponse(define=[], undefine=[garbage], reasoning='test')
	assert response.undefine == []

# Garbage string in undefine with valid options before Define keyword: Success
def test_garbage_define_keyword_with_prior_options():
	garbage = 'CONFIG_UBSAN, CONFIG_KASAN. Also check Define list: CONFIG_EXT4_FS'
	response = AgentResponse(define=[], undefine=[garbage], reasoning='test')
	assert response.undefine == ['CONFIG_UBSAN', 'CONFIG_KASAN']

# Garbage string in define with Undefine keyword: Success
def test_garbage_undefine_keyword_in_define():
	garbage = 'CONFIG_NET. Undefine CONFIG_KASAN'
	response = AgentResponse(define=[garbage], undefine=[], reasoning='test')
	assert response.define == ['CONFIG_NET']

# Valid response: Success
def test_valid_response():
	response = AgentResponse(define=['CONFIG_NET'], undefine=['CONFIG_OLD'], reasoning='needs net support')
	assert response.define == ['CONFIG_NET']
	assert response.undefine == ['CONFIG_OLD']
	assert response.reasoning == 'needs net support'
