from agent4.runner import is_ready, is_supported_ats


def candidate():
    return dict(status='PENDING',agent=4,channel='OFFICIAL_ATS',
      official_channel_url='https://jobs.ashbyhq.com/example/abc',
      channel_verified=True,master_resume_verified=True,
      variant_resume_qa_passed=True,review_status='PASS',qa_status='PASS',
      format_pass=True,source_pdf_verified=True,source_facts_verified=True,
      internal_score=97,uploaded=True,checksum_verified=True,
      eligibility='VERIFIED_INDIA_0_TO_2_YEARS',
      application_status='NOT_SUBMITTED',delivery_status='PENDING',blocked_recipient=False)


def test_ready_all_true():
    assert is_ready(candidate()) == (True,'READY')


def test_reject_mismatched_sha():
    c=candidate();c['checksum_verified']=False
    assert not is_ready(c)[0]


def test_reject_unverified_eligibility():
    c=candidate();c['eligibility']='REMOTE_REGION_UNVERIFIED'
    assert not is_ready(c)[0]


def test_reject_qa_under_97():
    c=candidate();c['internal_score']=96
    assert not is_ready(c)[0]


def test_reject_blocked_mailbox():
    c=candidate();c['blocked_recipient']=True
    assert not is_ready(c)[0]


def test_no_double_submit():
    c=candidate();c['delivery_status']='ATS_CONFIRMED'
    assert not is_ready(c)[0]


def test_reject_untrusted_domains():
    for url in ['https://jobs.ashbyhq.com.evil.tld/abc', 'http://jobs.lever.co/test',
                'https://example.com/apply', 'javascript:alert(1)']:
        assert not is_supported_ats(url)


def test_accept_official_ats_domains():
    assert is_supported_ats('https://jobs.lever.co/example/123/apply')
    assert is_supported_ats('https://job-boards.greenhouse.io/example/jobs/123')