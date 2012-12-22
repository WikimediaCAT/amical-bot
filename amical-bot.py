# -*- coding:utf-8 -*-
 
# -*- coding:utf-8 -*-
 
#-------------------------------------------------------------------------------
# Nom:         Amical-bot.
# Comentari:   Suport a la traducció d'articles. Vegeu manual a http://ca.wikipedia.org/wiki/Usuari:Amical-bot
#              Desenvolupat amb el finançament de la Fundació PuntCat.
#
# Autor:       Amical-Desenv1
#
# Creat:       1/03/2011
# Copyright:   (c) Amical Viquipèdia 2010
# Llicència:   GPL v2+
#-------------------------------------------------------------------------------
#!/usr/bin/env python
 
global idioma, pagina_er, usuari, pagina_origen	, titol_de_la_pagina
#Carrega mòduls
import wikipedia, codecs, re, catlib
import re
import  httplib, time, urllib
from time import strftime as date
global traduccions_fetes
traduccions_fetes = 0
 
def categ(idioma,categoria,q):
    #Donada una categoria en un idioma cerca la que li correspon en català.
	#Si no la troba, cerca categories pare fins a 5 nivells
    global llistacateg
    if q==5:
        return u''
    categoria = catlib.Category(wikipedia.getSite(idioma,"wikipedia"),categoria)
    if categoria.title() in llistacateg:
        return u''
    llistacateg.append(categoria.title())
    contingut = categoria.get()
    interwiki = re.compile("\[\[ca:([^\]]*)")
    try:
        return "[["+interwiki.findall(contingut)[0]+"]]\n"
    except:
        supercategories = categoria.supercategories()
        ret=u''
        for supercategoria in supercategories:
            ret+=categ(idioma,supercategoria.title(),q+1)
        return ret
 
def cerca_categories(idioma, pagina):
    #Retorna les categories en català a partir de les de l'article en l'idioma original
    #Ha de ser global per poder ser modificada i llegida tot i la recursivitat
    global llistacateg
    llistacateg=['']
    categories = pagina.categories()
    ret=u''
    for a in categories:
        ret+=categ(idioma,a.title(),1)
    return ret
 
def executa_er(pagina_amb_er, text):
	#Funció per executar sobre un text, les expressions regulars emmagatzemades en una pàgina
	troba_les_er=re.compile("(?<=\n\*).*")
	errors_trobats = re.compile("== Errors trobats ==")
	pagina = wikipedia.Page( wikipedia.getSite("ca","wikipedia"), pagina_amb_er)
	try:
		pagina_expressions = pagina.get()
	except:
		print u'la pàgina' +  pagina_amb_er + "no existeix"
		return text
	expressions=troba_les_er.findall(pagina_expressions)
	errors_ja_trobats = errors_trobats.findall(pagina_expressions) #Els errors ja s'han trobat en un altre traducció
	errors_nous = 0
	maxim=len(expressions)
	i=0
	#Cerca i substitueix cada una de les expresions regulars
	while i < maxim:
		try:
			titol = re.compile(expressions[i])
		except:
			if len(errors_ja_trobats)>0:
				if errors_nous == 0:
					pagina_expressions = pagina_expressions+"\n== Errors trobats ==\n"
					errors_nous = 1
				pagina_expressions = pagina_expressions + u"l'expressió regular '"+expressions[i]+u"' no s'ha pogut compilar\n"
				pagina.put(pagina_expressions,u"bot notificant error en expressió regular")
			i=i+2
			continue
		try:
			text = titol.sub(expressions[i+1],text)
		except:
			if len(errors_ja_trobats)>0:
				if errors_nous == 0:
					pagina_expressions = pagina_expressions+"\n== Errors trobats ==\n"
					errors_nous = 1
				pagina_expressions = pagina_expressions + u"l'expressió '"+expressions[i+1]+u"' ha donat error al substituir\n"
				pagina.put(pagina_expressions,u"bot notificant error en expressió regular")
		i=i+2
	return text
 
 
 
 
def contaparaules(cadena):
	#conta el nombre de paraules en una cadena
	anterior = 1
	paraules = 0
	for caracter in cadena:
		if caracter == ' ':
			blanc = 1
		else:
			blanc = 0
		if anterior == 1 and blanc == 0:
			paraules +=1
		anterior = blanc
	return paraules
 
def posaminuscules(text):
	#assegura que no hi ha cap paraula amb més de 1 majúscula, posant miníscules
	text2 = u''
	anterior = 0
	for caracter in text:
		if ema(caracter):
			if anterior == 0:
				anterior = 1
			else:
				caracter = caracter.lower()
		else:
			anterior = 0
		text2 = text2 + caracter
	return text2
 
 
def preprocessaenllacos(text):
	#transforma els enllaços dexant només el text visible canviant majúscules per minúscules excepte si tenen menys de 3 caracters
	#paraulestextuals guarda la llista de frases a efectes de debug per veure que es fa be l'encaix al text traduit
	global paraules, paraulestextuals, enllacosdefrase, forma
	minuscula = u"[abcdefghijklmnopqrstuvwxyzàáâäãăǎąåāæǣḃɓçćčćĉċuđḍďḋðèéêëẽēęḟƒĝġģğĥħìíîïīįĳĵķŀļḷḹľłñńňòóôöõøōǫœṗŗřṛṝşṡšŝßţṫṭÞùúûüŭūųẁŵẅƿýỳŷÿȳỹźžż]"
	majuscula = minuscula.upper()
	#treu la primera mitad dels enllaços
	p = re.compile('\[\[[^\|:\]#]*?\|')
	text2 = p.sub('[[',text)
	#assegura que no hi ha cap paraula amb més de 1 majúscula, posant miníscules
	text2 = posaminuscules(text2)
	#inverteix majúscules per minúscules i treu claudators en els enllaços
	q= re.compile('\[\[[^:\]]+\]\][a-zA-Z]*')
	enllacos = q.findall(text2)
	#troba les frases i els enllaços de cada frase
	cercafrase = re.compile('.*[\n\r]|.*\Z')
	frases = cercafrase.findall(text2)
	enllacosdefrase = []
	#omple la llista enllacos de frase amb el nombre d'enlaços de la la frase n per poder desfer els enlaços frase per frase i 
	#evitar que s'emboliquin.
	for frase in frases:
		llistaenllacos = q.findall(frase)
		enllacosdefrase.append(len(llistaenllacos))
	text3 = text2
	i = 0
	paraules = []
	paraulestextuals =[]
	forma =[]
	for enllac in enllacos:
		cercaPrimeresLletresDeCadaParaula = re.compile('\A.|(?<= ).')
		primereslletres = cercaPrimeresLletresDeCadaParaula.findall(enllac[2:])
		totmajuscules = 0
		for lletra in primereslletres:
			if lletra in majuscula:
				totmajuscules +=1
		if totmajuscules > 2:
			totmajuscules = 2
		substitueix = enllac.upper()
		#expressió regular per evitar que s'interpetin els metacaracters dins del enllaç
		r = re.compile('([\|\.\^\$\*\+\?\{\}\[\]\(\)])')
		enllac2 = r.sub('\\\\\\1',enllac)
		cerca = re.compile(enllac2)
		if enllac == substitueix or len(substitueix)<7:
			text3 = cerca.sub('[[('+format(i)+')|'+enllac[2:],text3,1)
			paraules.append(0)
			paraulestextuals.append(' ')
			forma.append(3)
		else:
			#treu els claudators
			t = re.compile('(.*)\]\](.*)')
			substitueix = t.sub(r"\1\2",substitueix[2:])
			text3 = cerca.sub(substitueix,text3,1)
			paraules.append(contaparaules(substitueix))
			paraulestextuals.append(substitueix)
			forma.append(totmajuscules)
		i +=1
	return text3
 
def ema(a):
	#torna veritat si el caracter és ma´júscules i fals altrament
	return a == a.upper() and not a == a.lower()
def emi(a):
	#torna veritat si el caracter és mainúscules i fals altrament
	return a == a.lower() and not a == a.upper()
def el(a):
	#torna veritat si el caracter és una lletra fals altrament
	return a.lower() != a.upper()
def comenca(a,lloc):
	#torna veritat si a la posició actual hi ha una lletra i les dues següent són majúscules
	return el(a[lloc]) and ema(a[lloc+1]) and ema(a[lloc+2])
 
def cerca_comencament(cadena,inici):
	#torna la primera posició de la cadena on una lletra esta seguida de dues majuscules.
	#Si no n'hi ha cap torna -1
	i = inici
	final = len(cadena)-2
	candidata = 0
	while i < final:
		if (  cadena[i] in ' \n' and (   ema(cadena[i+2])   or cadena[i+1] in '0123456789') ) and candidata == 0:
			candidata =i+1
		if comenca(cadena,i):
			if candidata == 0:
				return i
			else:
				return candidata
		if emi(cadena[i]) and emi(cadena[i+1]):
			candidata =0
		i+=1
	return -1
def cerca_final(cadena,inici):
	#torna la posició de la última lletra majúscula (o lúltim tancaparèntesis precedit d'una majúscula) tal que les dues següents són minúscules
	#comença per la segona lletra perquè la primera no és significativa ja que cal que la segona sigui majúscula
	#no cal preocupar-se de que n'hi hagi dures donç inici ja ho ha verificat
	i = inici+1
	#candidata conté la última majúscula o tancaparèntesi precedit de majúscula que s'ha trrobat
	candidata = inici +1
	final = len(cadena)
	#test indica el nombre de minúscules seguides que s'han trobat
	test = 0
	while i<final:
		#són candidates les majúscules precedides de lletra o els tancaparèntesis precedits de majúscula tota candidata nova posa a zero test
		if ( ema(cadena[i]) and el(cadena[i-1])) or ( cadena[i]==')' and ema(cadena[i-1])):
			candidata = i
			test = 0
		#tota minúscula quan ja es te una candidata incrementa el test tret de la "s" que la pot haver posat el bot per fer el plural
		elif emi(cadena[i]) and candidata != inici +1 and cadena[i] != 's' :
			test += 1
		#en trobar la segona minúscula sense cap canidata nova s'acaba la cerca
		if test == 2:
			return candidata
		i +=1
	return candidata
 
def contaparaules(cadena):
	#conta el nombre de paraules en una cadena
	anterior = 1
	paraules = 0
	for caracter in cadena:
		if caracter == ' ':
			blanc = 1
		else:
			blanc = 0
		if anterior == 1 and blanc == 0:
			paraules +=1
		anterior = blanc
	return paraules
 
def finalparaules(cadena,c,f,n):
	cadena = cadena[c:f]
	#troba la posició on acaba la nèssima paraula sempre n'hi ha d'haver més de les que es busca
	abansblanc = 1
	paraules = 0
	i = 0
	candidat = f-c
	for caracter in cadena:
		if caracter == ' ':
			abansblanc = 1
		else:
			if abansblanc == 1:
				abansblanc = 0
				paraules +=1
				if paraules > n:
					return candidat
		if el(caracter) or caracter == ')':
			candidat = i
		i +=1
 
 
 
 
def posamajuscula(a):
	return a.group(0).upper()
 
 
def posaenllacos(a,paraulestraduides, paraulestextuals,paraules,n,contadorbase):
	global forma
	#transoforma en mínúscules i hi posa clàudatosr d'enllaç només a les exptssions que tenen n paraules 
	contaparaulestextuals = 0
	for paraula in paraulestraduides:
		if contaparaulestextuals == len(paraulestextuals):
			continue
		if paraules[contaparaulestextuals] != n:
			contaparaulestextuals += 1
			continue
		try:
			cerca = re.compile(paraula+u'(?=[s\. ,;\n\'''r"!\?\:])')
		except:
			#cas que el text acabi amb tanca parèntesi cal millorar-ho perquè el parentesi no hauria de ser-hi
			#try:
			cerca = re.compile(paraula[0:-1]+u'\)(?=[s\. ,;\n\'''r"!\?\:])')
			#except:
			#	contaparaulestextuals += 1
			#	continue
		canvia_per = paraula.lower()
		if forma[contaparaulestextuals+contadorbase] == 1:
			canvia_per = canvia_per[0].upper()+canvia_per[1:]
		elif forma[contaparaulestextuals+contadorbase] == 2:
			cercaPrimeresLletresDeCadaParaula = re.compile('\A.|(?<= ).')
			canvia_per = cercaPrimeresLletresDeCadaParaula.sub(posamajuscula,canvia_per)
		if cerca.search(a):
#Reprodueix l'enllaç intern in li passa el nombre indicant l'ordre original en que venia
			a = cerca.sub('[[('+format(contaparaulestextuals+contadorbase)+')|'+canvia_per+']]',a,1)
#			a = cerca.sub('[['+paraula.swapcase()+']]',a,1)
			paraulestextuals[contaparaulestextuals] = ' '
			wikipedia.output(paraula)
		else:
			wikipedia.output(paraula)			
		contaparaulestextuals += 1
	return a, paraulestextuals
 
def afegeigenllac(a,b,comencament,anterior,contaparaulestextuals,final,paraulestextuals,paraulestraduides ):
	#afegeix a "b" un bocí de "a" trransformant-lo en un ellaç el format és [[(nobre d'ordre original)|text traduit]]
	global forma
	canvia_per = a[comencament:final+1].swapcase()
	if forma[contaparaulestextuals] == 1 and len(canvia_per) > 1 :
		canvia_per = canvia_per[0].upper()+canvia_per[1:]
	elif forma[contaparaulestextuals] == 2:
		cercaPrimeresLletresDeCadaParaula = re.compile('\A.|(?<= ).')
		canvia_per = cercaPrimeresLletresDeCadaParaula.sub(posamajuscula,canvia_per)
	if comencament > anterior:
		b=b+a[anterior:comencament]+'[[('+format(contaparaulestextuals)+')|'+canvia_per+']]'
	else:
		b=b+'[[('+format(contaparaulestextuals)+')|'+canvia_per+']]'
	return b
 
def postprocessaenllacos(a):
	#trenca els text en frases i el passa a postprocessar els enllaços frase a frase, d'aaquesta manera no es per el fil i si passa noés ne una frase.
	global paraules, paraulestextuals, paraulestraduides, enllacosdefrase
	cercafrases= re.compile('.*[\r\n]|.*\Z')
#	cercafrases= re.compile('\A.*|\n.*')
	frases = cercafrases.findall(a)
	i =0
	contaparaules =0
	b = ''
	maxim = len(enllacosdefrase)
	for frase in frases:
		if i >=maxim:
			continue
		if enllacosdefrase[i] > 0:
			final =contaparaules+enllacosdefrase[i]
			p = paraules[contaparaules:final]
			q = paraulestextuals[contaparaules:final]
			r = paraulestraduides[contaparaules:final]
			frase = postprocessaenllacos_boci(frase,p,q,r,contaparaules)
			contaparaules = final
		i+=1
		b = b+frase
	return b
 
 
 
def postprocessaenllacos_boci(a,paraules, paraulestextuals, paraulestraduides,contadorbase):
	#torna a invertit majuscules i minúscules i posa claudators als enllaços interns.
#	global paraules, paraulestextuals, paraulestraduides
	posicio = 0
	b = u''
	anterior=0
	descarta = 0
	contaparaulestextuals = 0
	#enllesteix traduccions idèntiques (aquelles que la traducció textual coincideix amb la traducció per separat)
	i = max(paraules)
	while i > 0:
		a,paraulestextuals = posaenllacos(a,paraulestraduides, paraulestextuals,paraules,i,contadorbase)
		i -=1
	contaparaulestextuals = 0	
	for nombreparaules in paraules:
		if paraulestextuals[contaparaulestextuals] == ' ':
			contaparaulestextuals+=1
			continue
		comencament = cerca_comencament(a,anterior)
		#si no n'hi ha mes acabar
		if comencament == -1:
			continue
		final = cerca_final(a,comencament)
		nombre = contaparaules(a[comencament:final+1])
		conta = 0
		while descarta >= nombre and conta < 10:
			conta +=1
			descarta = descarta - nombre
			b=b+a[anterior:comencament]+a[comencament:final+1].swapcase()
			anterior = final + 1
			comencament = cerca_comencament(a,anterior)
			final = cerca_final(a,comencament)
			nombre = contaparaules(a[comencament:final+1])
		if  nombre > nombreparaules:
			final = comencament + finalparaules(a,comencament,final+1,nombreparaules)
			b=afegeigenllac(a,b,comencament,anterior,contaparaulestextuals+contadorbase,final,paraulestextuals,paraulestraduides )
		elif nombre < nombreparaules:
			descarta = nombre - nombreparaules
			b=afegeigenllac(a,b,comencament,anterior,contaparaulestextuals+contadorbase,final,paraulestextuals,paraulestraduides )
		elif nombre == nombreparaules:
			b=afegeigenllac(a,b,comencament,anterior,contaparaulestextuals+contadorbase,final,paraulestextuals,paraulestraduides )
		contaparaulestextuals +=1
		anterior = final + 1		
 
	b = b+a[anterior:]
	return b
 
 
 
 
 
def preprocessa(text,pagina,grava=1):
	#preprocessa la pàgina previ a al traducció: 1) transforma enllaços interns en el codi de majúscules (omplint la taula de paraules per pode postprocessar,
	# 2) executa la pàgina Pre de expressions regulars per tal de canviar els metacaràcters que donen problemes 
	# 3) Subsitueix els símbols matemàtics i les lletre gregues pels sus codis unicode per tal que no desapareixin a al traducció.
	global paraules, paraulestextuals
	#Afegeix la llista de paraules dels enllaços per tenir-ne la traducció
	noutext = preprocessaenllacos(text)
	noutext = noutext + u"\nparaulesenllacos"
	for paraula in paraulestextuals:
		noutext = noutext + '\n\n' + paraula
	noutext = noutext+ "\n"
	noutext = executa_er("Usuari:Amical-bot/Pre", noutext)
	#noutext = wikipedia.UnicodeToAsciiHtml(noutext) #Treu els caractes matematics, lletrs greges etc que es perden al traduir
	re_math_signs = re.compile(ur"(ƒ|…|\+|−|⋅|×|\∗|÷|/|⇒|⇔|→|↦|⊦|⊥|⊤|⊣|⊢|⊨|⊩|⊫|⊬|⊭|⊮|⊯|∧|∨|∩|∪|±|∓|=|≟|≠|≡|≢|∼|≁|≂|≃|≄|≅|≌|≙|≈|≉|∝|∘|≤|≥|≪|≫|⟨+⟩|∅|∈|∋|∉|∌|⊆|⊇|⊊|⊋|⊄|⊅|∞|\∣|∤|∥|∦|⊕|⊖|⊗|⊙|°|′|″|ℕ|ℤ|ℚ|ℝ|ℂ|π|∀|∃|∄|∂|∆|∇|⁰|¹|²|³|⁴|⁵|⁶|⁷|⁸|⁹|⁺|⁻|⁼|⁽|⁾|ⁿ|ⁱ|¯|Α|α|Ά|ά|Β|β|Γ|γ|Δ|δ|Ε|ε|Έ|έ|Ζ|ζ|Η|η|Ή|ή|Θ|θ|Ι|ι|Ί|ί|Ϊ|ϊ|ΐ|Κ|κ|Λ|λ|Μ|μ|Ν|ν|Ξ|ξ|Ο|ο|Ό|ό|Π|π|Ρ|ρ|Σ|σ|ς|Τ|τ|Υ|υ|Ϋ|ϋ|Ύ|ύ|ΰ|Φ|φ|Χ|χ|Ψ|ψ|Ω|ω|Ώ|ώ|⊂)")
	math_signs = re_math_signs.findall(noutext)
	for math_sign in math_signs:
		noutext = noutext.replace(math_sign, wikipedia.UnicodeToAsciiHtml(math_sign))
	#Grava la pàgina modificada
	if grava == 1:
		pagina.put(noutext,u'bot preprocessant article previ a la traduccioo automatica')
		#cal verificar que efectivament s'ha gravat tornant a llegir, per exemple si hi ha un enllaç a una web de la llista negra no dona cap error però no la grava
		#text = pagina.get('','True')
		#if text != noutext:
		#	wikipedia.showDiff(text,noutext)
		#	return u"no s'ha pogut gravar"
	return noutext
 
def postprocessa(text,pagina):
	#desfa el preproces sobre el text traduït.
	global debug, paraulestraduides #, jaenunicode
	noutext = executa_er("Usuari:Amical-bot/Post", text)
	p = re.compile(u"paraulesenllacos([^:]*)")
	paraulesfinals = p.findall(noutext)
	print 'paraulesfinals', paraulesfinals
	noutext = p.sub('',noutext)
	noutext = noutext + '\n'
	q = re.compile('(?<=\n)[^\r\n]+')
	paraulestraduides = q.findall(paraulesfinals[0])
#	wikipedia.output(noutext)
#	print "<despres de tallar la cua"
	noutext = postprocessaenllacos(noutext)
#	prp = noutext
#	wikipedia.output(prp)
#	print "<despres de postprocessar els enllaços"
#	print "jaenunicode", jaenunicode
#	if jaenunicode == 0:
#		print 'ha entrat'
	noutext = wikipedia.html2unicode(noutext) #Torna a posar els caracters matemàtics, lletres gregues etc.
	#	wikipedia.output(noutext)
#	print "<despres de passar a unicode"
#	wikipedia.output(prp)
#	print "<prp"
#	res =input('?')
	#Grava la pàgina modificada	es pot eliminar quen ja funcioni i tornar el nou text
	if debug == 's' :
		pagina.put(noutext,u'bot postprocessant article despres de la traduccioo automatica')
	return noutext
 
 
def getGencat(title, lang):
	#funció per cridat el traducor automàtic de gencat torna el text del article traduit al català
	#si el traductor està fora de servei hauria de tornar ''
#    global jaenunicode
    print 1
    page   = wikipedia.Page(wikipedia.getSite('ca'), title)
    tr_dir = {"en": "ENGLISH-CATALAN", "fr": "FRENCH-CATALAN", "de": "GERMAN-CATALAN", "es": "SPANISH-CATALAN"}
    if lang not in tr_dir:
		return 'idioma no suportat'
    tr_dir = tr_dir[lang]
 
    url    = u"http://%s.org%s" % (
        ".".join(page.site().sitename().split(":")[::-1]),
        page.site().edit_address(page.urlname()).split("&useskin=monobook")[0]
    )
    url    = "http://%s.wikipedia.org/wiki/%s?action=edit" % ('ca', urllib.quote(title.encode("utf-8")))
    print 2
    params ={
        "translationDirection": tr_dir,
        "subjectArea": "GV",
        "MARK_ALTERNATIVES": "0",
        "url": url
    }
    params = urllib.urlencode(params)
    user_agent = "Mozilla/5.0 (Windows; U; Windows NT 6.0; ca; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5 GTB6"
    headers= {
        'User-Agent': user_agent,
        "Content-type": "application/x-www-form-urlencoded",
        "Accept": "text/plain",
    }
    data=None
    print 3
    print params
    retry=0
    while data is None:
        print 4
        try:
            conn = httplib.HTTPConnection('traductor.gencat.net')
            print 5
            conn.request("POST", "/url.do", params, headers)
            response = conn.getresponse()
            data = response.read()
        except KeyboardInterrupt:
            print 6
            print u"l'usuari ha cancel·lat"
            break
        except Exception, e:
            print 7
            print e, retry
            retry+=1
            retry_time = retry*2
            if retry_time>1:
                #retry_time =30
                return ''
            time.sleep(retry_time*60)
            if retry>=30:break
    textarea = re.compile(r"^.*<textarea[^>]*>(.+?)</textarea>.*$", re.DOTALL)
    data = textarea.sub(ur"\1", data)
#    jaenunicode = 0
    try:
        data = wikipedia.html2unicode(data)
        print "ha passat a unicode"
    except:
        print "no ha passat a uicode"
        resultat = ''
        jaenunicode = 1
        for caracter in data:
            try:
                caracter = wikipedia.html2unicode(caracter)
                resultat = resultat + caracter
            except:
               resultat = resultat + ' '
        data = resultat
    p = re.compile(u"paraulesenllacos([^:]*)")
    print p.findall(data)
    if len(p.findall(data))==0:
        return ''
    return data
 
def getLucy(title, lang):
	#funció per cridar el traducor automàtic de Lucy Software. Torna el text del article traduit al català
	#si el traductor està fora de servei hauria de tornar ''
    print 1
    page   = wikipedia.Page(wikipedia.getSite('ca'), title)
    tr_dir = {"en": "ENGLISH-CATALAN", "fr": "FRENCH-CATALAN", "de": "GERMAN-CATALAN", "es": "SPANISH-CATALAN"}
    if lang not in tr_dir:
		return 'idioma no suportat'
    tr_dir = tr_dir[lang]
 
    url    = u"http://%s.org%s" % (
        ".".join(page.site().sitename().split(":")[::-1]),
        page.site().edit_address(page.urlname()).split("&useskin=monobook")[0]
    )
    url    = "http://%s.wikipedia.org/wiki/%s?action=edit" % ('ca', urllib.quote(title.encode("utf-8")))
    print 2
    params ={
        "CREATE_CODING_LIST":	"0",
        "CREATE_GLOSSARY":	"0",
        "MARK_ALTERNATIVES":	"0",
        "MARK_COMPOUNDS":	"0",
        "MARK_CONSTANTS":	"0",
        "MARK_MEMORY":	"0",
        "MARK_UNKNOWNS":	"0",
        "PPM_USE":	"1",
        "TRANSLITERATE_UNKNOWNS":	"1",
        "translationDirection": tr_dir,
        "subjectArea": "GV",
        "url": url
    }
    params = urllib.urlencode(params)
    user_agent = "Mozilla/5.0 (Windows; U; Windows NT 6.0; ca; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5 GTB6"
    headers= {
        'User-Agent': user_agent,
        "Content-type": "application/x-www-form-urlencoded",
        "Accept": "text/plain",
    }
    data=None
    print 3
    print params
    retry=0
    while data is None:
        print 4
        try:
            conn = httplib.HTTPConnection('translendium.net','8080')
            print 5
            conn.request("POST", "/kwik_bare/url.do", params, headers)
            response = conn.getresponse()
            data = response.read()
        except KeyboardInterrupt:
            print 6
            print u"l'usuari ha cancel·lat"
            break
        except Exception, e:
            print 7
            print e, retry
            retry+=1
            retry_time = retry*2
            if retry_time>1:
                #retry_time =30
                return ''
            time.sleep(retry_time*60)
            if retry>=30:break
    textarea = re.compile(r"^.*<textarea[^>]*>(.+?)</textarea>.*$", re.DOTALL)
    data = textarea.sub(ur"\1", data)
    try:
        data = wikipedia.html2unicode(data)
        print "ha passat a unicode"
    except:
        print "no ha passat a unicode"
        resultat = ''
        jaenunicode = 1
        for caracter in data:
            try:
                caracter = wikipedia.html2unicode(caracter)
                resultat = resultat + caracter
            except:
               resultat = resultat + ' '
        data = resultat
    p = re.compile(u"paraulesenllacos([^:]*)")
    print p.findall(data)
    if len(p.findall(data))==0:
        return ''
    return data
 
 
 
 
 
 
''' funció recursiva per admetre infites redireccions
def llegeig redirigida(pagina)
	#llegeig una pàgina i trona el seu contingut o le de la pàgina a la que redirigeix
	try:
		# Carrega la pàgina
		contingut = page.get()
	except wikipedia.NoPage:
		# La pàgina no existeix
		return ''
	except wikipedia.IsRedirectPage, a:
		pagina_real = a[0]
		#treure # si n'hi ha
		p=re.compile('[^#]+')
		pagina_real = p.findall(pagina_real)[0]
		pagina_2 = wikipedia.Page( wikipedia.getSite(idioma,"wikipedia"), pagina_real)
		contingut = llegeig(pagina_2)
	return contingut
'''
 
 
 
 
def titol_catala(idioma,titol):
	#Funció per trobar el títol en català d'una pàgina donada en l'idioma origen
	#Si la pàgina en l'idioma oringinal no exiteix o no té interwiki en català retorna ''
	#Altrament retorna el títol de la pàgina en catalá en majúscules o minúscules segon estigui el títol de la pàina original.
	interwikicatala=re.compile("(?<=\[\[ca:)[^|\]]+")
	if titol == '' or titol == ' ':
		return ''
	page = wikipedia.Page( wikipedia.getSite(idioma,"wikipedia"), titol) 
	try:
		# Carrega la pàgina
		contingut = page.get()
	except wikipedia.NoPage:
		# L'enllaç en l'idioma original no existeix
		return ''
	except wikipedia.IsRedirectPage, a:
		pagina_real = a[0]
		#treure # si n'hi ha
		p=re.compile('[^#]+')
		pagina_real = p.findall(pagina_real)[0]
		pagina_2 = wikipedia.Page( wikipedia.getSite(idioma,"wikipedia"), pagina_real)
		contingut = pagina_2.get()
	except:
		return
	enllaccatala=interwikicatala.search(contingut)
	if enllaccatala:
		enllacara=enllaccatala.group(0)
		#posar la primera lletra en minúscules si l'enllaç original la tenia.
		if titol[0]==titol[0].lower():
			enllacara=enllacara[0].lower()+enllacara[1:]
		return enllacara
	else:
		#A l'article en lidioma original no hi ha interwiki al català
		return ''
 
 
def nouenllac(a):
	global enllacara
	#Per fer que no es repeteixi el nom del enllaç
	#Si la frase enllaçada i la frase traduïda són iguals construeix l'enllaç sense repetir
	if enllacara != a.group(1):
		return '[['+enllacara+r'|'+a.group(1)+']]'
	else:
		return '[['+enllacara+r']]'
 
def tradueixenllacos(idioma,text,text_desti,paginadesti):
	global enllacara
	noutext = text
	noutext_desti = text_desti
	#Per estalviar temps i accessos a la base de dades, les pàgines ja consultades s'emmagatzemen en un diccionari que es 
	#reinicia cada cop que es tradueix un article nou (per no omplir massa la memòria.
	#inicialitza un diccionari per no consultar repetides vegades el mateix article
	diccionari ={}
 
	#Prepara expressions regulars
	'''
	* p : és una expressió regular per trobar enllaços interns comença per dos claudators, 
	      segueix per una cadena de qualsevol caracter sense sense :  per evitar agafar imatges, 
	      categories i interwikis i acaba amb dos claudators es posa el ? per evitar que empalmi dos
	      enllaços interns diferents
	* parentesis i tancaparentesis : per cercar parèntesis
	* cerca : per agafar la cadena amb el nom de l'article eliminant els claudators, el | i el #
 
	'''
	p = re.compile('(\[\[[^:]*?]])')
	parentesis=re.compile("[\(]")
	tancaparentesis=re.compile("[\)]")
	cerca=re.compile("[^[#|\]]+") 
	q = re.compile('\[\[\((.*)\)\|.*\]\]')
 
	#Trobar tots els elnllaços interns de la pagina a traduir
	enllacos=p.findall(text)
	maxim = len(enllacos)
 
	#Trobar tots els elnllaços interns de la pagina destí
 
#	enllacos_desti=p.findall(text_desti)
#	maxim_desti = len(enllacos_desti)
	#Intenta traduir cada un dels enllaços
	i=0
	while i < maxim:#and i < maxim_desti:
		print u'Enllaços fets:', i, 'de:', maxim
		#Li treu els claudators i el | es queda amb el nom de l'article
		enllac=cerca.search(enllacos[i])
#		enllac_desti=cerca.search(enllacos_desti[i])
		i=i+1
		try:
		# en cas que falli el nombre de enllaços perquè no avorti el bot.
		#S'hauria de repassar per evitar l'error cas de que el text visible del enllaç és "$US" falla
			llegir=enllac.group(0)
		except:
			continue
#		llegir_desti=enllac_desti.group(0)
		#Si ja està al diccionari (ja s'ha traduit abans aquest ellaç intern) l'agafa del dicconari altrament el cerca i el fica al diccionari
		if llegir in diccionari:
			enllacara = diccionari[llegir]
		else:
			enllacara = titol_catala(idioma,llegir)
			diccionari[llegir]=enllacara
		if enllacara != '': #and enllacara != llegir_desti:
			r = re.compile('\[\[\('+format(i-1)+'\)\|([^\]]*)\]\]')
			noutext_desti = r.sub(nouenllac,noutext_desti)
		else:
			r = re.compile('\[\[\('+format(i-1)+'\)\|([^\]]*)\]\]')
			noutext_desti = r.sub(r'[[\1]]',noutext_desti)
#			llegir_desti = parentesis.sub(r'[\\(]',llegir_desti,1)
#			llegir_desti = tancaparentesis.sub(r'[\\)]',llegir_desti)
#			canviar=re.compile("(?<=\[\[)"+llegir_desti)
			#Substitueix el nom de l'artice enllçat en l'altre idioma pel nom en català respectant el text visible del traductor
#			noutext_desti = canviar.sub(enllacara+'|'+llegir_desti,noutext_desti,1)
	#Grava la pàgina modificada	(es pot eliminar quent vagi be el programa
	if debug == 's' :
		paginadesti.put(noutext_desti,u'bot traduint automaticament enllaços interns')	
	return noutext_desti
 
 
def treubarres(cadena):
		#treu barres verticals que estiguin entre {{ o [[ dins d'una cadena donada subtitunint-les per "çç" respecta les que estiguin fora
		cadenadesti = ''
		max = len(cadena)
		i = 0
		claudators=0
		claus = 0
		while i < max:
			if cadena[i]=='{':
				claus = claus +1
			elif cadena[i]=='[':
				claudators = claudators +1
			elif cadena[i]==']':
				claudators = claudators -1
			elif cadena[i]=='}':
				claus = claus -1
			if (claus <3 and claudators == 0) or cadena[i] != '|':
				cadenadesti = cadenadesti + cadena[i]
			else:
				cadenadesti = cadenadesti + u'çç'
			i=i+1
		return cadenadesti
 
 
def separa_nom_de_valor(text,ultima):
	#torna una llista de dues cadenes amb el nom i el valor del paràmetre, si no hi ha = el nom es buit si és lúltim paràmetre treu els }} del final.
	#compte amb plantilles en el valor de paràmetres d'altres plantilles. només fa cas del primer =
	i=0
	max = len(text)
	resultat = ['','']
	ultimalletra = ''
	nom = 1
	while i<max:
		if nom == 1:
			if text[i]!='=':
				resultat[0] =resultat[0]+text[i]
			else:
				nom = 0
				i = i+1
				continue
		else:
			resultat[1] = resultat[1] + text[i]
		i=i+1
	#Si no s'ha trobat = és tot valor i no té nom
	if nom == 1:
		resultat[1] = resultat[0]
		resultat[0] = ''
	if ultima:
		#Si és l'últim paràmetre de la plentilla li treu les dues claus de tancament
		resultat[1] = resultat[1][0:-2]
	return resultat
 
 
 
def omple_diccionari(idioma):
	#omple els diccionaris necessaris per traduir les plantilles i amb els errors ja trobats abans
	#expressió regular per separar la part de definició de la part de errors
#	p = re.compile(u'[.\n]*== Errors ==[.\n]*')
	global traduccio_titol, traduccio_variable, tractament_variable
	global error_titol, error_variable, error_tractament_variable
	global errorsanteriors, tractament, errorsnous
	errorsnous = 0
	error_titol = {}
	error_variable = {}
	error_tractament_variable = {}
	#llegeix pàgina amb les instruccons del  tractament de plantilla
	paginatractament = wikipedia.Page( wikipedia.getSite('ca',"wikipedia"), 'Usuari:Amical-bot/Plantilles/'+idioma)  
	tractament = paginatractament.get()
	posicioerrors = tractament.find(u'== Errors ==')
	if posicioerrors == -1:
		diccionari_en_tractament(tractament)
		errorsanteriors = ''
	else:
		errorsanteriors = tractament[posicioerrors + 13:]
		tractament = tractament[0:posicioerrors-1]
		diccionari_en_tractament(errorsanteriors)
		error_titol = traduccio_titol
		error_variable = traduccio_variable 
		error_tractament_variable = tractament_variable
		diccionari_en_tractament(tractament)
	return	
 
 
 
def gravaerrors(idioma):
	global errorsanteriors, tractament, errorsnous, traduccio_titol
	global error_titol, error_variable, error_tractament_variable
	if errorsnous == 0:
		return
	errors = u''
	for titol in error_titol:
		errors = errors + u'\n{"' + titol + u'" : "' + error_titol[titol] + u'"}\n'
	if len(error_variable)>0:
		for titol in error_variable:
			primeravariable = 1
			for variable in error_variable[titol]:
				if primeravariable == 1:
					primeravariable = 0
					if titol in traduccio_titol:
						errors = errors + u'\n<nowiki>{"' + titol + u'" : "' + traduccio_titol[titol]  + '"['
					else:
						errors = errors + u'\n<nowiki>{"' + titol + u'" : "traducció plantilla no definida"['
				nomoriginal=variable
				nomvar=error_variable[titol][variable]
				errors = errors + u'("' + nomoriginal + u'", "' + nomvar + u'"'
				if variable in error_tractament_variable[titol]:
					errors = errors + u', "' + error_tractament_variable[titol][variable] + u'")'
					error_tractament_variable[titol][variable] = 'fet'
				else:
					errors = errors + u', "")'
			errors = errors + u']}</nowiki>\n'
	if len(error_tractament_variable)>0:
		for titol in error_tractament_variable:
			primeravariable = 1
			for variable in error_tractament_variable[titol]:
				if error_tractament_variable[titol][variable] == 'fet':
					continue
				if primeravariable == 1:
					errors = errors + u'\n<nowiki>{"' + titol + u'" : "' + traduccio_titol[titol]  + '"['
					primeravariable = 0
				errors = errors + u'("' + variable + u'", "", "' + error_tractament_variable[titol][variable] + u'")'
			if primeravariable == 0:
				errors = errors + u']}</nowiki>\n'
	paginatractament = wikipedia.Page( wikipedia.getSite('ca',"wikipedia"), 'Usuari:Amical-bot/Plantilles/'+idioma) 	
	paginatractament.put(tractament + '\n== Errors ==' + errors)
	return
 
 
def diccionari_en_tractament(tractament):
	#cerca les definicions de plantilles escrites en "tractament" i omple diccionaris
	global traduccio_titol, traduccio_variable, tractament_variable
	cerca_plantilles = re.compile('{.*?}')
	plantilles = cerca_plantilles.findall(tractament)
	cerca_nom_i_parametres = re.compile('(?:{ *")(.+?)" *: *"(.+?)"(?:.*\[)(.+?)(?:\]})')
	cerca_parametres = re.compile(' *" *(.*?) *" *, *" *(.*?) *" *, *" *(.+?) *" *')
	#('(?:\(")(.+)(?:",")(.+?)(?:",")(.+?)(?:"\))')
	#(' *" *(.*?) *" *, *" *(.*?) *" *, *" *(.+?) *" *')
 
	#inicialitza diccionaris
	traduccio_titol = {}
	traduccio_variable = {}
	tractament_variable = {}
	print 'plantilles', plantilles
	for plantilla in plantilles:
		nom_nom_i_parametres = cerca_nom_i_parametres.findall(plantilla)
		print 'nom_nom_i_parametres', nom_nom_i_parametres
		contaparametres = 0
		for data in nom_nom_i_parametres:
			traduccio_titol[data[0]] = data[1]
			if len(data) > 2:
				parametres = cerca_parametres.findall(data[2])
				diccionari_traduccio = {}
				diccionari_tractament = {}
				for parametre in parametres:
					if parametre[0] == '':
						contaparametres = contaparametres + 1
						nomvariable = contaparametres
					else:
						nomvariable = parametre[0]
					diccionari_traduccio[nomvariable] = parametre[1]
					diccionari_tractament[nomvariable] = parametre[2]
				traduccio_variable[data[0]] = diccionari_traduccio
				tractament_variable[data[0]] = diccionari_tractament
	return
 
def trobaplantilles(text):
	#Dóna una llista de les plantilles que hi ha en un text tenint en compte les indentades
 
	#p és una expressió regular per trobar plantilles (admet multilínea) i un nivell d'indentació de plantilles
	#p1 és per trobar les plantilles dins d'una plantilla, cal cercar a partir del tercer caracter de la cadena per no trobar els {{ del començament
	p = re.compile(('(?:{{[^{^}]+)(?:{{[^{^}]+}}[^{^}]*)*(?:}})')) 
	p1 = re.compile('{{[^{}]*}}')
 
	#Trobar totes les plantilles de primer nivell
	plantilles=p.findall(text)
	maxim = len(plantilles)
	#trobar les plantilles indentades
	i=0
	while i < maxim :
		plantilles_indentades = p1.findall(plantilles[i][2:])
		if len(plantilles_indentades)>0:
			plantilles = plantilles+plantilles_indentades
		i = i+1
	return plantilles
 
def treuespaisinewline(text):
	#treu espais abans i despres sún text i un salt de línea de despres, retorna si hi havia salt de lineaa o no.
	saltalinea = 0
	if len(text) == 0:
		return saltalinea,''
	while text[-1] == ' ' or text[-1] == '\n':
		if text[-1] == '\n':
			saltalinea = 1
		text = text[0:-1]
	#treure espais al començament del txt
	if len(text) == 0:
		return saltalinea,''
	while text[0] == ' ' or text[0] == '\n':
		if text[0] == '\n':
			saltalinea = -1
		text = text[1:]	
	return saltalinea,text
 
 
def errordeplantilles(nomplantilla,nom_variable,error):
	#En detectar un error en les instruccions de traducció d'una plantilla (manca de definició de com fer la traducio)
	#Mira si ja s'havia detectat abans aquest error i si no l'afegeix a la llista d'errors detectats per tal de poder-lo escriure
	#Avisant a la pàgina de definició de traduccions de plantilles.
	global error_titol, error_variable, error_tractament_variable
	global errorsnous
	if error == 'plantilla no definida':
		if not nomplantilla in error_titol:
			errorsnous=1
			error_titol[nomplantilla] = u'traducció plantilla no definida'
	elif error == 'variable no definida':
		if not nomplantilla in error_variable: #si hi hi ha diccionari d'errors per la plantilla, inicialitzal
			error_variable[nomplantilla] = {}
		if not nom_variable in error_variable[nomplantilla]:
			errorsnous = 1
			error_variable[nomplantilla][nom_variable] = u'traducció variable no definida'
	elif error == 'tractament no definit':
		if not nomplantilla in error_tractament_variable: #si hi hi ha diccionari d'errors, inicialitzal
			error_tractament_variable[nomplantilla] = {}
		if not nom_variable in error_tractament_variable[nomplantilla]:
			errorsnous = 1
			error_tractament_variable[nomplantilla][nom_variable] = u'tractament variable no definit'
	return
 
 
def tradueixplantilles(idioma,text,text_desti,paginadesti):
	#Tradueix les plantilles seguint les instrucions de la pàgina segons idioma
	'''Prepara expressions regulars
	q és una ER per trobar el nom de la plantilla
	r per trobar les variables
	t2 per tornar a posar els | entra claudatos es cerca els çç
	'''
	q = re.compile('(?<={{)[^\|}]*')
	# ER antiga '(?<=\|)[^\|}]+(?=[\|}])' descarta claudators de plantilles indentades, ho modifico tenint en compte que els claudators de la inicial no s fan servir
	r = re.compile('(?<=\|)[^\|]+')
	t2 = re.compile(u'çç')
	cadena2='|'
 
	#Trobar totes les plantilles de les pagines origen i destí
	plantilles = trobaplantilles(text)
	maxim = len(plantilles)
	plantilles_desti=trobaplantilles(text_desti)
	maxim_plantilles_desti = len(plantilles_desti)
 
	#si maxim_desti i maxim no són iguals avisar??
 
	#Omple dicionaris
	omple_diccionari(idioma)
 
	#Intenta traduir cada una de les plantilles
	i=0
	while i < maxim and i < maxim_plantilles_desti:
		print u'Plantilles fetes', i, 'de:', maxim
		plantilla = plantilles[i]
		plantilla_desti = plantilles_desti[i]
		#treu | entre claudators de plantilla i de plantilladesti
		plantilla = treubarres(plantilla)
		plantilla_desti = treubarres(plantilla_desti)
		nomplantilla = q.findall(plantilla)[0]
		#compila expressio regular de la plantilla desti per poder-la substituir
		pre_er_plantilla_desti = plantilles_desti[i]
		# substituir "metacaracter" per \"metacaracter"
		barres = re.compile('([\|\.\^\$\*\+\?\{\}\[\]\(\)])')
		pre_er_plantilla_desti = barres.sub('\\\\\\1',pre_er_plantilla_desti)
		er_plantilla_desti = re.compile(pre_er_plantilla_desti)
		#treue salt de línia i espais del nom de la plantilla i apuntar si hi ha salt de línia
		saltalinea,nomplantilla = treuespaisinewline(nomplantilla)
		#si la plantilla no té instruccions per traduir-la deixa la original i continua
		#posal el títol de la plantilla en majúscules
		nomplantilla = nomplantilla[0].upper()+nomplantilla[1:]
		if not(nomplantilla in traduccio_titol):
			text_desti = er_plantilla_desti.sub(plantilles[i],text_desti)
			i = i+1
			#mirar si l'error ja s'havia detectat i si no afegir-lo a la llista
			errordeplantilles(nomplantilla,'','plantilla no definida')
			continue
		#tradueix el títol de la plantilla
		plantilla_traduida = u'{{'+traduccio_titol[nomplantilla]
		if saltalinea == 1:
			plantilla_traduida = plantilla_traduida + '\n'
		#tradueix i tracta les variables
		#troba les variables
		variables = r.findall(plantilla)
		variables_desti = r.findall(plantilla_desti)
		maxim_variables = len(variables)
		#POTSER CALDRIA AVISAR DE REVISAR LA TRADUCCIÓ SI NO QUADREN.
		maxim_desti = len(variables_desti)
		j = 0
		#inicialitza cntavariables que serveix per les variables sense nom
		contavariables = 1
		while j < maxim_variables:
			variable = variables[j]
			#treu els salts de línia al final de les variables i apunta si cal inserir salt de línia o no
			if variable[-1] == "\n":
				saltalinea = 1
				variable = variable[0:-1]
			else:
				saltalinea = 0
			if j < maxim_desti:
				variable_desti = variables_desti[j]
			else:
				variable_desti = variable
			if variable_desti[-1] == "\n":
				variable_desti = variable_desti[0:-1]
			#separa nom i valor (si hi ha un = on no hi ha nom falla)
			dades_variable = separa_nom_de_valor(variable, j==maxim_variables-1)
			dades_variable_desti = separa_nom_de_valor(variable_desti, j==maxim_variables-1)
			if dades_variable[0] != '': #s'ha trobat un = i s'ha pogut separa nom de valor
				#elimina espais en blanc al començament i al final del nom
				a,nom_variable = treuespaisinewline(dades_variable[0])
				if a == -1 :
					plantilla_traduida = plantilla_traduida + '\n'
				#en aquest cas el valor de la variable és el del altre cantó del signe =
				valor_variable = dades_variable[1]
				valor_variable_desti = dades_variable_desti[1]
				#vigilar si no esta definida la variable
				if nom_variable in traduccio_variable[nomplantilla]:
					plantilla_traduida = plantilla_traduida + '|'+traduccio_variable[nomplantilla][nom_variable] +' = '
				else:
					plantilla_traduida = plantilla_traduida + '|'+nom_variable +' = '
					#mira si l'error ja s'havia detectat i si no afegeix-lo a la llista
					errordeplantilles(nomplantilla,nom_variable,'variable no definida')
			else: #No hi ha = el contingut correspon al valor
				valor_variable = dades_variable[1]
				valor_variable_desti = dades_variable_desti[1]
				#valor_variable = variable
				#valor_variable_desti = variable_desti
				nom_variable = repr(contavariables)
				contavariables = contavariables + 1				
				plantilla_traduida = plantilla_traduida + '|'
				try:
					xx = traduccio_variable[nomplantilla][nom_variable]
					if traduccio_variable[nomplantilla][nom_variable] != '':
						#Si en català es vol que tingui nom el paràmetre
						plantilla_traduida = plantilla_traduida + traduccio_variable[nomplantilla][nom_variable] +' = '
				except:
					xx = ''
			if nom_variable in tractament_variable[nomplantilla]:
				#vigilar si no esta definida la variable
				tractament = tractament_variable[nomplantilla][nom_variable]
			else:
				tractament = 'N'
				errordeplantilles(nomplantilla,nom_variable,'tractament no definit')
			if tractament == 'N':
				plantilla_traduida = plantilla_traduida + valor_variable
			elif tractament == 'S':
				plantilla_traduida = plantilla_traduida + valor_variable_desti
			elif tractament == 'TEI':
				titol = titol_catala(idioma,valor_variable)
				if titol == '':
					plantilla_traduida = plantilla_traduida + valor_variable_desti
				else:
					try :
						plantilla_traduida = plantilla_traduida + titol	
					except :
						plantilla_traduida = plantilla_traduida + valor_variable+"*"
			if saltalinea == 1:
				plantilla_traduida = plantilla_traduida + '\n'
			j = j+1
		plantilla_traduida = plantilla_traduida + '}}'
		i = i+1	
 
		#torna a posar els | en lloc dels çç entre claudators i subplantilles
		plantilla_traduida = t2.sub(cadena2, plantilla_traduida)
		#print 'plantilla_traduida: ', plantilla_traduida
		#a = input('?')
		#substitueix la plantilla per la seva traducció
		text_desti = er_plantilla_desti.sub(plantilla_traduida,text_desti)
	#Grava la pàgina modificada	
	if debug == 's' :
		paginadesti.put(text_desti,u'bot traduint automaticament plantilles')
	gravaerrors(idioma)
	return text_desti
 
 
 
def intercala(idioma,text,text_desti,paginadesti,pagina_original):
	#Intercala el text original amb el traduït, excepte a partir de categories i fórmules matemàtiques que no estan en migg del text
	global usuari, data_origen, versio_origen, categoria_traduida, intercalar, pagina_2
	#p és una expressió regular per trobar els salts de línia
	p = re.compile('.*?\n|.*\Z')
	#q és per trobar les línies que només tenen expressions matemàtiques. q1 comença, q2 acaba
	q1 = re.compile('\A:? *<[Mm]ath>')
	q2 = re.compile('</[Mm]ath>')
	formula = 0
 
	#clau és per trobar les claus de plantilles
	clau1 = re.compile('{')
	clau2 = re.compile('}')
	plantilles_obertes = 0
 
	#preparar per aturar-se en arribar a les categories
	projecte = wikipedia.getSite(idioma)
	prou = 0
 
	#Trobar tots els parragrafs de la pagina orignal
	parragraforiginal=p.findall(text)
	maxim = len(parragraforiginal)
 
	#Trobar tots els parragrafs de la pagina traduida
	parragraftraduida=p.findall(text_desti)
	maxim_desti = len(parragraftraduida)
	print maxim, maxim_desti
	#Intercala els parragrafs de la pàgina traduida i la pàgina original
	i=0
	j=0
	resultat=''
	pendent = ''
	categories_trad = cerca_categories(idioma,pagina_2)
	while i < maxim:
		plantilles_abans = plantilles_obertes
		if formula == 0 :
			plantilles_obertes = plantilles_obertes + len(clau1.findall(parragraforiginal[i]))-len(clau2.findall(parragraforiginal[i]))
		if j < maxim_desti and prou == 0 and formula == 0 and plantilles_obertes == 0 :
			if intercalar != 'No':
				if plantilles_abans != 0 :
					resultat=resultat+parragraforiginal[i]+"\n"+pendent + parragraftraduida[j]
					pendent = ''
				else :
					resultat=resultat+parragraforiginal[i]+"\n"+parragraftraduida[j]
			else :
				resultat=resultat+parragraftraduida[j]
		else:
			if formula == 1:
				if len(q2.findall(parragraforiginal[i])) > 0:
					formula = 0
			if categoria_traduida == '' or len(wikipedia.getCategoryLinks(parragraforiginal[i],projecte))==0:
				#les categories només es posen si no s'està fent una tradcucció en bloc d'raticles d'una categoria
				resultat=resultat+parragraforiginal[i]
				if plantilles_obertes != 0 :
					if j < maxim_desti :
						pendent = pendent + parragraftraduida[j]
		i=i+1
		j=j+1
		#Aturar-se en arribar a les categories
		if i < maxim:
			if len(wikipedia.getCategoryLinks(parragraforiginal[i],projecte))>0:
				#en arribar a categories si és traducció d'un grup d'una categoria posaar la categoria
				if prou == 0 and categoria_traduida != '':
					resultat = resultat + "\n" + '[[Categoria:'+categoria_traduida+']]'
				if prou == 0 and categoria_traduida == '':
					resultat = resultat + "\n" + categories_trad
				prou=1
			if len(q1.findall(parragraforiginal[i])) > 0:
				formula = 1
	#posa plantilla de traducció i interwiki al idioma original
	plantilla = u'{{Traducció|' + idioma + '|' + pagina_original + '}}\n'
	interwiki = '\n[[' + idioma + ':' + pagina_original + ']]'
	if intercalar != 'No':
		#La plantilla de traducció només es posa si s'intercala.
		resultat = plantilla + resultat + interwiki
	else:
		resultat = resultat + interwiki
	#Grava la pàgina modificada	
	p=re.compile('/\d+')
	titol_de_la_pagina = paginadesti.title()
	titol_pagina_general =p.sub('',titol_de_la_pagina)
	if titol_pagina_general != titol_de_la_pagina and intercalar != "No":
		#Si és una subpàgina amb titol numero
		resultat = resultat + u"\n{{Traduït de|" + idioma + u"|" + pagina_original + u"|" + data_origen + u"|" + versio_origen + u"}}\n"
	if debug == 's' :
		paginadesti.put(resultat,u'bot intercalant text original amb text traduït')
	else:
		paginadesti.put(resultat,u"traducció automàtica feta a petició de [[" + usuari + u"]] pendent de revisió per l'usuari")
	if not ":" in paginadesti.title():
		#Si la pàgina que es tradueix és de l'espai de noms, posa la platilla "traduït de" a la discussió
		pagina_discusio = wikipedia.Page( wikipedia.getSite("ca","wikipedia"), u"Discussió:"+paginadesti.title())
		pagina_discusio.put(u"{{Traduït de|" + idioma + u"|" + pagina_original + u"|" + data_origen + u"|" + versio_origen + u"}}\n--~~~~\n",u"traducció automàtica feta a petició de [[" + usuari + u"]]")
		#pagina_discusio.put(u"{{Traduït de|"+idioma+u"|"+pagina_original+u"}}\n--~~~~\n",u"traducció automàtica feta a petició de [[" + usuari + u"]]")
	return resultat
 
 
def arreglatraduccio(text,pagina_er,pagina):
	noutext = text
	if pagina_er != '':
		noutext = executa_er(pagina_er, text)
	if noutext != text:
		#Grava la pàgina modificada	
		if debug == 's' :
			pagina.put(noutext,u'bot arreglant traducció automàtica amb les er de [['+ pagina_er +']]')
	return noutext
 
 
def trobaparametres(pagina):
	#trobal els paràmetres de la plantilla de la pàgina i llegeix la pàgina a traduir ({{[^{^}]+}}[^{^}]*)*
	global idioma, pagina_er, usuari, pagina_origen, pagina_original, titol_de_la_pagina, data_origen, versio_origen, maxim_articles, mida_maxima, categoria_traduida, intercalar, pagina_2
	mida_maxima = 0
	categoria_traduida = ''
	intercalar = 'Si'
	plantilla = re.compile('(?<=\[\[)Usuari[ _][Dd]iscu[^\|\]]*(?=[\|\]])')
	text = pagina.get() #cal llegir-la perquè funcioni el mètode pagina.userName
	ultim_que_ha_escrit = pagina.userName()
	parametres = pagina.templatesWithParams()
	print parametres
	if len(parametres) == 0:
		#No hi ha plantilla, algú ha posat aquesta categoria a un article sense posar la plantilla
		categoria = re.compile(u'.*[[.*Categoria:.*Peticions de.*traducci. autom.tica.*]].*')
		text = pagina.get()
		text = categoria.sub('',text)
		pagina.put(text, u'bot el·lininant la categoria de petició de traduccuó: manca de plantilla')
		return 'no hi ha plantilla'
	idioma = parametres [0][1][0]
	print idioma
 
	pagina_original = parametres [0][1][1]
	pagina_er = ''
	usuari = ''
	if len(parametres [0][1])==3:
		pagina_er = u"Usuari:Amical-bot/er-omissió/" + idioma
		usuari_avisa = plantilla.findall(parametres [0][1][2])
		if len(usuari_avisa) > 0:
			usuari = usuari_avisa[0]
		else:
			usuari = usuari_avisa
	elif len(parametres [0][1])>3:
		pagina_er = parametres [0][1][2]
		if pagina_er == '':
			pagina_er = u"Usuari:Amical-bot/er-omissió/" + idioma
		wikipedia.output(parametres [0][1][3])
		usuari_avisa = plantilla.findall(parametres [0][1][3])
		if len(usuari_avisa) > 0:
			usuari = usuari_avisa[0]
		else:
			usuari = usuari_avisa
	if len(parametres [0][1])==8:
		#cas de petició de traducció d'un grup d'articles dins d'una categoria
		maxim_articles = int(parametres [0][1][4])
		mida_maxima = 999999
		mida_maxima = int(parametres [0][1][5])
		categoria_traduida = parametres [0][1][6]
		intercalar = parametres [0][1][7]
	try:
		pagina_expressions = wikipedia.Page( wikipedia.getSite('ca',"wikipedia"), pagina_er) 
	except:
		#no existeix la pàgina de er
		print u"pàgina ER no s'ha trobat s'assigna la que hi ha per omisió", pagina_er
		pagina_er = u"Usuari:Amical-bot/er-omissió/" + idioma
	try:
		pagina_usuari = wikipedia.Page( wikipedia.getSite('ca',"wikipedia"), usuari) 
	except:
		#no està signada la petició
		print 'usuari no trobat', usuari
		usuari = u"Usuari Discussió:" + ultim_que_ha_escrit
		pagina_usuari = wikipedia.Page( wikipedia.getSite('ca',"wikipedia"), usuari) 
		#return 'no hi ha usuari'		
	pagina_2 = wikipedia.Page( wikipedia.getSite(idioma,"wikipedia"), pagina_original) 
	try:
		pagina_origen = pagina_2.get()
	except wikipedia.NoPage:
		#La pàgina no existeix
		#treure la plantilla
		text = pagina.get()
		plantilla2 = re.compile('{{.*[Pp]etici. de traducci..*}}')
		text = plantilla2.sub('', text)
		avisar_usuari('no hi ha pagina origen', titol_de_la_pagina)
		pagina.put(text, u'bot el·lininant la plantilla de petició de traduccuó: manca pàgina en idioma original')
		return 'no hi ha pagina origen'
	except wikipedia.IsRedirectPage, a:
		pagina_original = a[0]
		pagina_2 = wikipedia.Page( wikipedia.getSite(idioma,"wikipedia"), pagina_original)
		pagina_origen = pagina_2.get()
	print 'idioma, pagina_er, usuari, pagina_original'
	if usuari[17] in '0123456789':
		#El nom d'usuari comença per un nombre (suposo que és una IP)
		#treure la plantilla
		text = pagina.get()
		plantilla2 = re.compile('{{.*[Pp]etici. de traducci..*}}')
		text = plantilla2.sub('', text)
		pagina.put(text, u"bot el·lininant la plantilla de petició de traduccuó: petició de traduccuó feta per un anònim")
		return 'Petició de traduccuó feta per un anònim'		
	data_origen = repr(pagina_2.editTime())
	data_origen = data_origen[0:4]+"/"+data_origen[4:6]+"/"+data_origen[6:8]+" "+data_origen[8:10]+"h "+data_origen[10:12]+"' "+data_origen[12:14]+"''"
	versio_origen = repr(pagina_2.latestRevision())
	wikipedia.output(idioma)
	wikipedia.output(pagina_er)
	wikipedia.output(usuari)
	wikipedia.output(pagina_original)
 
 
 
 
def avisar_usuari(missatge, titol_de_la_pagina):
	#deixa un missatge a la pàgina de discussió del usuari informant del proces de les seves peticions
	global idioma, pagina_er, usuari, pagina_origen, pagina_original
	if missatge == 'traductor_down':
		resultat = u" no s'ha pogut completar perquè en aquest moment el traductor automàtic no està disponible, es tornarà a intentar més tard. Si voleu podeu traduir-la amb un altre traductor automàtic i canviar la plantilla a 'Petició de tradució c' llavors el robot amical-bot continuarà el postprocés."
	elif missatge == 'preproces fet':
		resultat = u" s'ha preprocessat. Heu d'emprar un traductor automatic extern per traduir-lo del {{" +  idioma + u"}} donat que el traductor intern no el té incorporat, en acabar canvieu la plantilla a 'Petició de tradució b' llavors el robot amical-bot continuarà el postprocés."
	elif missatge == 'fet':
		resultat = u" s'ha completat amb èxit."
	elif missatge == 'no hi ha pagina origen':
		resultat = u" no es pot fer perquè no existeix la pàgina sol·licitada en l'idioma origen."
	elif missatge == u"no s'ha pogut gravar":
		resultat = u"el sistema no permet gravar la còpia de la pàgina original, provablement sigui perquè hi ha un enllaç de la llista negra, podeu detectar-ho intentant gravar una còpia de la pàgina original en una pàgina de proves, llavors resoleu el problema modificant la pàgina en l'idioma original i torneu a fer la petició de traducció"
	missatge = u"\n== Petició de traducció ==\n*La vostra petició de traducció de l'article [[" + titol_de_la_pagina + "]]" + resultat+ u'--~~~~\n'
	pagina = wikipedia.Page( wikipedia.getSite('ca',"wikipedia"), usuari) 
	p = re.compile(u'\n== Petició de traducció ==\n')
	pagina_discusio = pagina.get()
	if p.search(pagina_discusio):
		pagina_discusio = p.sub(missatge,pagina_discusio,1)
	else:
		pagina_discusio = pagina_discusio+missatge
	pagina.put(pagina_discusio,u'bot enviant missatge sobre petició de traducció automàtica', minorEdit =False)
 
 
 
def despresdetraduccioautomatica(traduit,pagina, titol_de_la_pagina):
	#acaba la feina despres de la acció d'un traductor automatic
	global traduccions_fetes, idioma, pagina_origen, pagina_er, pagina_original
	postprocessat = postprocessa(traduit,pagina)
	enllactraduit = tradueixenllacos(idioma,pagina_origen,postprocessat,pagina)
	plantillatraduida = tradueixplantilles(idioma,pagina_origen,enllactraduit,pagina)
	traduccioarreglada = arreglatraduccio(plantillatraduida,pagina_er,pagina)
	text = intercala(idioma,pagina_origen,traduccioarreglada,pagina,pagina_original)
	#mirar si és una petició en bloc. Cal garantr que els únic nombres són els de creació de pàgina.
	p=re.compile('/\d+')
	titol_pagina_general =p.sub('',titol_de_la_pagina)
	traduccions_fetes = traduccions_fetes + 1
	if titol_pagina_general == titol_de_la_pagina:
		#no és una subpàgina
		avisar_usuari('fet', titol_de_la_pagina)
	else:
		#és una subpàgina
		#posar-hi el títol
		text = "\n=" + pagina_original.title() +"=\n"+text
		pagina.put(text,"'bot posant el titol de la pagina orignal dins del text")
		pagina_general = wikipedia.Page( wikipedia.getSite('ca',"wikipedia"), titol_pagina_general)
		manquen_traduir = int(pagina_general.get()) -1
		if manquen_traduir > 0:
			pagina_general.put(format(manquen_traduir),'bot actualitzant nombre de traducions fetes')
		else:
			#S'ha acabat la traducció en bloc, cal enganxar-les totes.
			conta = 0
			text = ''
			final = 'no'
			while final == 'no':
				conta +=1
				titol_subpagina = titol_pagina_general+'/'+format(conta)
				subpagina = wikipedia.Page( wikipedia.getSite('ca',"wikipedia"), titol_subpagina)
				try:
					textpagina = subpagina.get()
					text = text + textpagina
					if textpagina == '':
						final = 'si'
					subpagina.put('',u"bot blanquejant la subpàgina, les dades s'adjunten a la pàgina")
				except:
					final = 'si'
			pagina_general.put(text,u'bot posant el contingut de totes les subpàgines a la pàgina general')
			avisar_usuari('fet', titol_pagina_general)
	print traduccions_fetes
 
def fespeticions(pagina_origen,pagina_original,idioma,usuari):
	global pagina_er,maxim_articles, mida_maxima, categoria_traduida, intercalar,titol_de_la_pagina
	#llegeis les pàgines de la categoria i crea peticons de les que no tinguem i que siguin de menys de 3k
	projecte = wikipedia.getSite(idioma)
	cat = catlib.Category(projecte, pagina_original)
	pagines = cat.articles()
	contador = 1
	for pagina in pagines:
		titol = pagina.title()
		try:
			contingut = pagina.get()
		except:
			#no és una pàgina sinó una redirecció 
			continue
		if len(contingut)>mida_maxima:
			continue
		if titol_catala(idioma,titol) != '':
			continue
		paginanova = wikipedia.Page( wikipedia.getSite('ca',"wikipedia"), titol)
		contingut = u"{{Petició de traducció|"+idioma+"|"+titol+"|"+pagina_er+"|[["+usuari+"]]|"+ format(maxim_articles) +"|"+ format(mida_maxima) +"|"+ categoria_traduida +"|"+ intercalar +"}}"
		try:
		#només la crea si no existeix. si existeix és que a la wiki en l'idioma original no hi ha la interwiki al català, es podria posar.
			x = paginanova.get()
			continue
		except:
			#gravar-l en una subpàgina
			titol_subpagina = titol_de_la_pagina + "/"+format(contador)
			subpagina = wikipedia.Page( wikipedia.getSite('ca',"wikipedia"), titol_subpagina)
			subpagina.put(contingut,u'bot fent petició de traducció per encarrec de '+usuari)
		contador +=1
		if contador > maxim_articles:
			return contador-1
	return contador -1
 
 
 
def buidarpeticionsnoves():	
	global idioma, pagina_er, usuari, pagina_origen, pagina_original, titol_de_la_pagina
	#tradueix les pàgines de la categoria "Peticions de còpia i preprocés per traducció automàtica" si gencat esta down les preprocessa i la 
	#passa a la categoria "Peticions de traducció automàtica" canviant la plantilla
	projecte = wikipedia.getSite()
	cat = catlib.Category(projecte, u"Categoria:Peticions de còpia i preprocés per traducció automàtica")
	pagines = cat.articles()
	for pagina in pagines:
		titol_de_la_pagina = pagina.title()
		if titol_de_la_pagina == u'Lady Gaga':
			continue
		if titol_de_la_pagina == u'Plantilla:Petició de traducció' or titol_de_la_pagina == u'Plantilla:Petició de traducció/ús' :
			continue
		wikipedia.output(titol_de_la_pagina)
		resultat = trobaparametres(pagina)
		if resultat == 'no hi ha plantilla' or resultat == 'no hi ha pagina origen' or resultat == 'no hi ha usuari' or resultat == "Petició de traduccuó feta per un anònim":
			print resultat
			continue
		#copia la pàgina original sobre la actual, va be per poder veure la diferencia amb el preprocessat
		if u'Category:' in pagina_original or u'Categoría:' in pagina_original or u'Catégorie:' in pagina_original or 'Kategorie:' in pagina_original :
			#si en comptes d'una pàgina és una categoria es creen peticions de traducció de tots els articles de menys de 3k
			peticions_fets = fespeticions(pagina_origen,pagina_original,idioma,usuari)
			text = pagina.get()+"\n"
			text = treuprimeraplantilla(text)+format(peticions_fets)
			pagina.put(text,u"bot treu plantilla de petició de traducció d'una categoria ja processada")
			continue
		if debug == 's' :
			pagina.put(pagina_origen,u"bot copiant article de {{"+idioma+"}}[[W:"+idioma+":"+pagina_original+"]]")
		preprocessada = preprocessa(pagina_origen,pagina)
		if preprocessada == u"no s'ha pogut gravar":
			avisar_usuari("no s'ha pogut gravar",titol_de_la_pagina)
			plantilla = u"{{ Petició de traducció a|" + idioma + "|" + pagina_original + "|" + pagina_er + "| [[" + usuari + "]] }}\n"
			preprocessada = plantilla + treuprimeraplantilla(preprocessada) + u"\n '''''NO S'HA POGUT TRADUIR PERQUÈ EL SISTEMA NO PERMET GRAVAR LA PÀGINA ORIGINAL PROBABLEMENT SIGUI PERQUÈ TÉ ENLLAÇOS A PÀGINES DE LA LLISTA NEGRA RESOLEU EL PROBLEMA I TORNEU A POSAR LA PLANTILLA DE PETICIÓ '''''"
			pagina.put(preprocessada,u"bot canviant plantilla, preprocés fet")
			continue
		traduit = getGencat(titol_de_la_pagina, idioma)
		if traduit == '' :
			traduit = getLucy(titol_de_la_pagina, idioma)
		if traduit == 'idioma no suportat':
			# No s'ha traduit perquè l'idioma no està suportat, canviar plantilla a "a"
			plantilla = u"{{ Petició de traducció a|" + idioma + "|" + pagina_original + "|" + pagina_er + "| [[" + usuari + "]] }}\n"
			preprocessada = plantilla + treuprimeraplantilla(preprocessada)
			pagina.put(preprocessada,u"bot canviant plantilla, preprocés fet")
			avisar_usuari('preproces fet',titol_de_la_pagina)
			continue	
		if traduit != '':
			if debug == 's' :
				pagina.put(traduit,u"bot traduint article al català")
			despresdetraduccioautomatica(traduit,pagina, titol_de_la_pagina)
		else:
			#No s'ha traduït perquè el traductor està fora de servei canviar plantilla a "b"
			plantilla = u"{{ Petició de traducció b|" + idioma + "|" + pagina_original + "|" + pagina_er + "| [[" + usuari + "]] }}\n\n"
			preprocessada = plantilla + treuprimeraplantilla(preprocessada)
			#MANCA GRAVAR LA TAULA DE paraules PER PODER RECUPARAR ELS ENLLAÇOS ITERNS DESPRES DE LA TRADUCCIÓ
			pagina.put(preprocessada,u"bot canviant plantilla per interrupció del servei de traducció")
			avisar_usuari('traductor_down',titol_de_la_pagina)
			continue
 
 
def treuprimeraplantilla(text):
    #treu la plantilla de petició de traducció i només deixa el que hi ha al darrete
    p = re.compile(r"{{.*Petici. de traducci.*}}")
    text = p.sub('', text)
    p = re.compile(r"\A *\n")
    text = p.sub('', text)
    return text
 
 
def buidarpeticionsinterrompudes():
	#Torna a intentar la traducció amb gencat i acabar el procés de les pàgines a la categoria: "Peticions de traducció automàtica"
	global idioma, pagina_er, usuari, pagina_origen, pagina_original
	projecte = wikipedia.getSite()
	cat = catlib.Category(projecte, u"Categoria:Peticions de traducció automàtica")
	pagines = cat.articles()
	for pagina in pagines:
		titol_de_la_pagina =pagina.title()
		if titol_de_la_pagina == u'Plantilla:Petició de traducció b' or titol_de_la_pagina == u'Plantilla:Petició de traducció b/ús' :
			continue
		resultat = trobaparametres(pagina)
		if resultat == 'no hi ha plantilla' or resultat == 'no hi ha pagina origen' or resultat == 'no hi ha usuari':
			continue
		#Per si s'ha modificat la pàgina al idioma original convindria llegir la còpia que es va gravar o lligar-ho a una verssió fixa.
		preprocessada = preprocessa(pagina_origen,pagina,0) #l'executa per tornar a carregar els diccionaris, peró no torna a gravar.
		traduit = getGencat(titol_de_la_pagina, idioma)
		if traduit == '':
			traduit = getLucy(titol_de_la_pagina, idioma)
		if traduit != '':
			traduit = treuprimeraplantilla(traduit)
			if debug == 's' :
				pagina.put(traduit,u"bot traduint article al català")
			despresdetraduccioautomatica(traduit,pagina,titol_de_la_pagina)
 
def buidarpeticionspendentspostproces():			
	#Acaba el postprocés de les pàgines a la categoria: "Peticions de postprocés després d'una traducció automàtica"
	#És el cas que l'usuari hagi emprat un traductor automatic alternatiu i hagi canviat la plantilla a "c"
	global idioma, pagina_er, usuari, pagina_origen, pagina_original
	projecte = wikipedia.getSite()
	cat = catlib.Category(projecte, u"Categoria:Peticions de postprocés després d'una traducció automàtica")
	pagines = cat.articles()
	for pagina in pagines:
		titol_de_la_pagina =pagina.title()
		if titol_de_la_pagina == u'Plantilla:Petició de traducció c' or titol_de_la_pagina == u'Plantilla:Petició de traducció c/ús' :
			continue
		resultat = trobaparametres(pagina)
		if resultat == 'no hi ha plantilla' or resultat == 'no hi ha pagina origen' or resultat == 'no hi ha usuari':
			continue
		preprocessada = preprocessa(pagina_origen,pagina,0) #l'executa per tornar a carregar els diccionaris, peró no torna a gravar.
		traduit = pagina.get()
		traduit = treuprimeraplantilla(traduit)
		#Per si s'ha modificat la pàgina al idioma original convindria llegir la còpia que es va gravar o lligar-ho a una verssió fixa.
		despresdetraduccioautomatica(traduit, pagina, titol_de_la_pagina)
 
 
def principal():
	global debug, traduccions_fetes
	debug = ''
	while debug!='s' and debug!='n':
		debug = raw_input('Grava cada pas?')
	while 1==1:
		buidarpeticionsnoves()
		buidarpeticionsinterrompudes()
		buidarpeticionspendentspostproces()
		print "Traduccuions fetes: ", traduccions_fetes
		time.sleep(60)
 
principal()
 
def prova_plantilles():
	global idioma, pagina_er, usuari, pagina_origen, pagina_original
	projecte = wikipedia.getSite()
	cat = catlib.Category(projecte, u"Categoria:Peticions de postprocés després d'una traducció automàtica")
	pagines = cat.articles()
	for pagina in pagines:
		titol_de_la_pagina =pagina.title()
		if titol_de_la_pagina == u'Plantilla:Petició de traducció c' or titol_de_la_pagina == u'Plantilla:Petició de traducció c/ús' :
			continue
		resultat = trobaparametres(pagina)
		if resultat == 'no hi ha plantilla' or resultat == 'no hi ha pagina origen' or resultat == 'no hi ha usuari':
			continue
		traduit = pagina.get()
		traduit = treuprimeraplantilla(traduit)
		plantillatraduida = tradueixplantilles(idioma,pagina_origen,traduit,pagina)
		traduccioarreglada = arreglatraduccio(plantillatraduida,pagina_er,pagina)
		intercala(idioma,pagina_origen,traduccioarreglada,pagina,pagina_original)
		#avisar_usuari('fet', titol_de_la_pagina)
 
#prova_plantilles()
def provaintercala():
	global idioma, pagina_er, usuari, pagina_origen, pagina_original
	projecte = wikipedia.getSite()
	cat = catlib.Category(projecte, u"Categoria:Peticions de postprocés després d'una traducció automàtica")
	pagines = cat.articles()
	for pagina in pagines:
		titol_de_la_pagina =pagina.title()
		if titol_de_la_pagina == u'Plantilla:Petició de traducció c' or titol_de_la_pagina == u'Plantilla:Petició de traducció c/ús' :
			continue
		resultat = trobaparametres(pagina)
		if resultat == 'no hi ha plantilla' or resultat == 'no hi ha pagina origen' or resultat == 'no hi ha usuari':
			continue
		traduit = pagina.get()
		traduit = treuprimeraplantilla(traduit)
		intercala(idioma,pagina_origen,traduit,pagina,pagina_original)
 
 
#provaintercala()
