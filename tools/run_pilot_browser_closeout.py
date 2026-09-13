"""Real Chromium against temporary pilot fixtures; never production or providers."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3
from playwright.sync_api import sync_playwright, expect
from tools.pilot_closeout_fixture import pilot_server


def run(output: Path) -> dict:
    output.mkdir(parents=True,exist_ok=True)
    checks=[]
    def passed(name): checks.append({'check':name,'status':'PASS'})
    with pilot_server() as (base,data,root), sync_playwright() as p:
        executable=os.environ.get('NUTEV_CHROMIUM_EXECUTABLE')
        browser=p.chromium.launch(**({'executable_path':executable} if executable else {}),args=['--no-sandbox'])
        contexts=[]
        diagnostics=[]
        network=[]
        def page_in(context):
            page=context.new_page()
            page.on('pageerror',lambda e:diagnostics.append(str(e)))
            page.on('request',lambda req:network.append({'event':'request','url':req.url,'method':req.method}))
            page.on('response',lambda res:network.append({'event':'response','url':res.url,'status':res.status}))
            page.on('requestfailed',lambda req:network.append({'event':'failed','url':req.url,'reason':req.failure}))
            return page
        def login(page,label):
            user=data['users'][label]
            page.goto(base+'/login.html',wait_until='domcontentloaded')
            expect(page.locator('#loginForm')).to_be_visible()
            page.locator('#loginEmail').fill(user['email']);page.locator('#loginPassword').fill(user['password'])
            page.locator('#loginSubmit').click();page.wait_for_url(base+'/',timeout=10000)
            return user
        def authenticate(page,label):
            user=login(page,label)
            expect(page.locator('#nutevWorkspaceSelect')).to_be_visible()
            with page.expect_navigation(wait_until='domcontentloaded'):
                page.locator('#nutevWorkspaceSelect').select_option(user['workspace_id'])
            expect(page.locator('#nutevWorkspaceSelect')).to_have_value(user['workspace_id'])
            expect(page.locator('#nutevProjectSelect')).to_be_enabled()
            with page.expect_navigation(wait_until='domcontentloaded'):
                page.locator('#nutevProjectSelect').select_option(user['projects'][0])
            expect(page.locator('#nutevProjectSelect')).to_have_value(user['projects'][0])
            page.goto(base+'/evidence-library.html',wait_until='domcontentloaded')
            page.locator('#libraryScope').select_option('project')
            expect(page.locator('#libraryStateMessage')).to_contain_text('Nenhum artigo')
            expect(page.locator('#libraryHealth')).to_have_text('projeto atual')
            expect(page.locator('#libraryScope')).to_have_value('project')
        def controlled_search_start_failure(page,status,message,*,keyboard=False):
            calls=[]
            def fail(route):
                calls.append({'method':route.request.method,'url':route.request.url})
                route.fulfill(status=status,content_type='application/json',body=json.dumps({'error':'synthetic_failure','message':message}))
            page.route('**/api/search/jobs',fail)
            try:
                page.locator('#question').fill(f'controlled browser failure {status}')
                if keyboard:
                    page.locator('#question').press('Control+Enter')
                else:
                    page.locator('#searchBtn').click()
                expect(page.locator('#searchState')).to_contain_text(message,timeout=10000)
                expect(page.locator('#searchBtn')).to_be_enabled()
                expect(page.locator('#globalSearchBtn')).to_be_enabled()
                assert calls==[{'method':'POST','url':base+'/api/search/jobs'}],calls
            finally:
                page.unroute('**/api/search/jobs',fail)
        def select_only_provider(page,provider_id):
            details=page.locator('details.advanced')
            if details.count() and not bool(details.evaluate('el=>el.open')):
                details.locator('summary').click()
            boxes=page.locator('#providerGrid input[type=checkbox]')
            expect(boxes.first).to_be_visible()
            found=False
            for index in range(boxes.count()):
                box=boxes.nth(index);selected=(box.get_attribute('value') or '')==provider_id
                found=found or selected
                if selected and not box.is_checked():box.check()
                elif not selected and box.is_checked():box.uncheck()
            assert found,f'provider not found: {provider_id}'
        def assert_mobile_surface(page,label,path):
            page.goto(base+path,wait_until='domcontentloaded')
            toggle=page.locator('.mobile-nav-toggle')
            expect(toggle).to_be_visible(timeout=10000)
            if toggle.get_attribute('aria-expanded')!='true':toggle.click()
            expect(toggle).to_have_attribute('aria-expanded','true')
            overflow=float(page.evaluate('document.documentElement.scrollWidth-innerWidth'))
            assert overflow<=2.0,f'{label}: mobile horizontal overflow {overflow}px'
            page.screenshot(path=str(output/f'mobile-{label}.png'),full_page=True)
            passed(f'mobile_{label}_navigation_and_no_horizontal_overflow')
        try:
            for _ in range(2):
                context=browser.new_context(viewport={'width':1366,'height':900})
                context.route('**/*',lambda route:route.continue_() if route.request.url.startswith(base) else route.abort())
                contexts.append(context)
            a=page_in(contexts[0]);b=page_in(contexts[1])
            authenticate(a,'a');authenticate(b,'b');passed('two_users_login_workspace_project')
            a.locator('#manualArticleEntry summary').click()
            a.locator('#libraryArticleId').fill(data['article_id']);a.locator('#libraryNotes').fill('PRIVATE_A_BROWSER')
            a.locator('#saveLibraryPlacement').click();expect(a.locator('#libraryEntries')).to_contain_text('PRIVATE_A_BROWSER')
            b.reload(wait_until='domcontentloaded');b.locator('#libraryScope').select_option('project')
            expect(b.locator('#libraryEntries')).not_to_contain_text('PRIVATE_A_BROWSER');passed('global_identity_private_placement')
            a.locator('[data-fulltext-article]').click()
            expect(a.locator('[data-fulltext-status]')).to_have_text('Nenhum acesso ativo a texto completo neste contexto.')
            passed('fulltext_permission_empty_state')
            a.screenshot(path=str(output/'library-desktop.png'),full_page=True)
            tab=page_in(contexts[0]);tab.goto(base+'/project.html',wait_until='domcontentloaded')
            tab.locator('#nutevProjectSelect').select_option(data['users']['a']['projects'][1])
            expect(tab.locator('#nutevProjectSelect')).to_have_value(data['users']['a']['projects'][1])
            expect(a.locator('#nutevProjectSelect')).to_have_value(data['users']['a']['projects'][1])
            a.locator('#libraryScope').select_option('project')
            expect(a.locator('#libraryEntries')).not_to_contain_text('PRIVATE_A_BROWSER')
            passed('same_session_two_tabs_context_invalidation')
            a.goto(base+'/project.html?project_id='+data['users']['b']['projects'][0],wait_until='domcontentloaded')
            expect(a.locator('#nutevProjectSelect')).to_have_value(data['users']['a']['projects'][1])
            a.go_back(wait_until='domcontentloaded');a.reload(wait_until='domcontentloaded')
            a.locator('#libraryScope').select_option('project')
            expect(a.locator('#libraryEntries')).not_to_contain_text('PRIVATE_A_BROWSER')
            passed('foreign_deep_link_back_and_reload')
            pending=[]
            def hold(route):
                response=route.fetch();pending.append((route,response))
            a.route('**/api/library?scope=project&hold=1',hold)
            a.evaluate("void (window.delayedResult=fetch('/api/library?scope=project&hold=1').then(r=>r.json()).then(()=>window.stalePaint=true).catch(()=>false))")
            for _ in range(100):
                if pending:break
                a.wait_for_timeout(50)
            assert pending,'delayed response not intercepted'
            user=data['users']['a']
            response=contexts[0].request.post(base+'/api/context/select',data={'workspace_id':user['workspace_id'],'project_id':user['projects'][0]});assert response.status==200
            pending[0][0].fulfill(response=pending[0][1])
            expect(a.locator('#nutevProjectSelect')).to_have_value(user['projects'][0]);assert a.evaluate('window.stalePaint !== true')
            passed('delayed_response_cannot_paint_after_context_change')
            a.goto(base+'/exports.html',wait_until='domcontentloaded')
            payload={'export_kind':'fixture','artifacts':[{'name':'fixture.txt','media_type':'text/plain','content_text':'PRIVATE_EXPORT_BROWSER'}]}
            response=contexts[0].request.post(base+'/api/exports',data=payload);assert response.status==201,response.text()
            export_id=response.json()['export']['id']
            a.locator('#refreshExports').click();expect(a.locator('[data-manifest]')).to_be_visible()
            a.locator('[data-manifest]').click();expect(a.locator('[data-manifest-panel]')).to_contain_text('fixture.txt')
            assert contexts[1].request.get(base+f'/api/exports/{export_id}/artifacts/fixture.txt').status==404
            assert contexts[0].request.get(base+f'/api/exports/{export_id}/artifacts/fixture.txt').body()==b'PRIVATE_EXPORT_BROWSER'
            passed('export_manifest_download_and_foreign_denial')

            a.goto(base+'/search.html',wait_until='domcontentloaded');expect(a.locator('#searchBtn')).to_be_enabled();passed('pilot_search_page_loaded')
            controlled_search_start_failure(a,429,'Limite sintético de busca atingido. Tente novamente em instantes.')
            expect(a.locator('#searchState')).to_have_attribute('class','error')
            passed('search_start_429_is_visible_and_does_not_repost')
            controlled_search_start_failure(a,503,'Busca temporariamente indisponível no teste controlado.',keyboard=True)
            expect(a.locator('#searchState')).to_have_attribute('class','error')
            passed('keyboard_ctrl_enter_503_uses_same_fail_safe_surface')

            select_only_provider(a,'pubmed')
            a.locator('#question').fill('offline provider disabled browser acceptance')
            a.locator('#searchBtn').click()
            expect(a.locator('#summary')).to_be_visible(timeout=20000)
            expect(a.locator('#summary')).to_contain_text('A busca não recuperou resultados utilizáveis',timeout=5000)
            outcome=a.locator('#summary').inner_text().casefold()
            assert 'indisponibilidade ou lacunas' in outcome,outcome
            assert 'cobertura descreve recuperação das fontes, não qualidade, certeza ou elegibilidade da evidência' in outcome,outcome
            passed('offline_provider_failure_is_not_presented_as_no_evidence')

            a.set_viewport_size({'width':390,'height':844})
            for label,path in (
                ('search','/search.html'),
                ('project','/project.html'),
                ('library','/evidence-library.html'),
                ('review','/review.html'),
                ('exports','/exports.html'),
            ):
                assert_mobile_surface(a,label,path)
            passed('core_mobile_surface_matrix')

            a.goto(base+'/evidence-library.html',wait_until='domcontentloaded');tab.goto(base+'/project.html',wait_until='domcontentloaded');tab.locator('#nutevLogoutButton').click();tab.wait_for_url('**/login.html');a.wait_for_url('**/login.html');passed('logout_invalidates_other_tab')
            with sqlite3.connect(data['database']) as con:con.execute("UPDATE platform_auth_sessions SET expires_at='2000-01-01T00:00:00+00:00' WHERE user_id=?",(data['users']['b']['user_id'],))
            b.bring_to_front();b.evaluate("window.dispatchEvent(new Event('focus'))");b.wait_for_url('**/login.html',timeout=10000);passed('session_expiry_clears_visible_private_page')

            orphan_context=browser.new_context(viewport={'width':1366,'height':900});orphan_context.route('**/*',lambda route:route.continue_() if route.request.url.startswith(base) else route.abort());contexts.append(orphan_context)
            orphan=page_in(orphan_context);login(orphan,'orphan')
            expect(orphan.locator('.context-guidance')).to_contain_text('Acesso ainda não provisionado')
            expect(orphan.locator('.context-guidance')).to_contain_text('administrador do NutEV')
            orphan.goto(base+'/project.html',wait_until='domcontentloaded');expect(orphan.locator('#projectState')).to_contain_text('Acesso ainda não provisionado');passed('first_login_without_workspace_explains_next_step')

            onboarding_context=browser.new_context(viewport={'width':1366,'height':900});onboarding_context.route('**/*',lambda route:route.continue_() if route.request.url.startswith(base) else route.abort());contexts.append(onboarding_context)
            onboarding=page_in(onboarding_context);new_user=login(onboarding,'onboarding')
            onboarding.locator('#nutevWorkspaceSelect').select_option(new_user['workspace_id']);expect(onboarding.locator('#nutevProjectSelect')).to_be_enabled()
            onboarding.locator('#nutevProjectSelect').select_option(new_user['projects'][0]);onboarding.wait_for_load_state('domcontentloaded')
            onboarding.goto(base+'/project.html',wait_until='domcontentloaded')
            expect(onboarding.locator('#templatePanel')).to_be_visible();expect(onboarding.locator('#templatePanel')).to_contain_text('Escolha como este projeto vai usar o NutEV')
            expect(onboarding.locator('input[name="applicationTemplate"]')).to_have_count(3)
            onboarding.locator('input[name="applicationTemplate"][value="GENERIC_EVIDENCE_PROJECT"]').check();onboarding.locator('#configureApplication').click();onboarding.wait_for_load_state('domcontentloaded')
            expect(onboarding.locator('#projectHealth')).to_have_text('contexto configurado');expect(onboarding.locator('#projectModules')).to_contain_text('Buscar evidências');expect(onboarding.locator('#projectModules')).to_contain_text('Biblioteca');expect(onboarding.locator('#projectModules')).to_contain_text('Exportações');passed('first_project_configuration_has_clear_supported_next_actions')

            assert not diagnostics,diagnostics;passed('no_javascript_page_errors')
        except Exception as exc:
            (output/'pilot-browser.json').write_text(json.dumps({'status':'FAIL','checks':checks,'error':str(exc),'fixture_only':True,'production_contacted':False},indent=2)+'\n')
            for index,context in enumerate(contexts):
                for number,page in enumerate(context.pages):
                    try:page.screenshot(path=str(output/f'failure-{index}-{number}.png'),full_page=True)
                    except Exception:pass
            raise
        finally:
            (output/'browser-network.json').write_text(json.dumps(network,indent=2)+'\n');(output/'page-errors.json').write_text(json.dumps(diagnostics,indent=2)+'\n');(output/'server.log').write_bytes((root/'server.log').read_bytes())
            for context in contexts:context.close()
            browser.close()
    report={'status':'PASS','checks':checks,'checks_passed':len(checks),'fixture_only':True,'production_contacted':False,'external_providers_contacted':False}
    (output/'pilot-browser.json').write_text(json.dumps(report,indent=2)+'\n');return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=Path('browser_e2e_artifacts/pilot'))
    args=parser.parse_args();print(json.dumps(run(args.output),indent=2))


if __name__=='__main__':main()
